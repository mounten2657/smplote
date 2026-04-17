import gevent
from retrying import retry
from tool.core import Logger, Ins, Config, Str, Time, Attr, Error
from tool.db.cache.redis_client import RedisClient
from tool.db.cache.redis_task_keys import RedisTaskKeys

logger = Logger()
redis = RedisClient()
redis_conn = redis.client


@Ins.singleton
class RedisTaskQueue:
    """基于 RQ 的分布式任务队列. - LIFO"""

    ARGS_UNIQUE_KEY = True
    GREENLETS = []
    PROCESS = []

    def win_consumer(self, qn):
        """windows 环境下的队列消费"""
        while True:
            gevent.sleep(0.1)
            res = redis_conn.blpop(qn, timeout=3)
            if not res:
                continue
            _, task_str = res
            task_data = Attr.parse_json_ignore(task_str)
            task_spec = task_data['task_spec']
            args = task_data['args']
            kwargs = task_data['kwargs']
            RedisTaskQueue._execute_task(task_spec, *args, **kwargs)

    @staticmethod
    @retry(stop_max_attempt_number=2, wait_exponential_multiplier=1000)
    def _execute_task(task_spec: str, *args, **kwargs) -> bool:
        """队列消费执行"""
        try:
            action = Attr.get_action_by_path(task_spec)
            logger.debug(f"正在执行队列任务: {task_spec}", 'RTQ_TASK_EXEC_PAR')
            res = action(*args, **kwargs)
            logger.debug(f"队列任务执行结果[: {res}", 'RTQ_TASK_EXEC_RET')
            return True
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(
                f"Task[{task_spec}] failed  - {err}",'RTQ_TASK_RETRY')
            raise

    @staticmethod
    def add_task(sk, *args, **kwargs):
        """往队列中添加任务"""
        service = RedisTaskKeys.RTQ_QUEUE_LIST.get(sk)
        service_name = service.get('s')
        queue_num = service.get('n')
        if not service_name:
            raise ValueError(f'Not register service - {sk}')
        i = Str.randint(1, queue_num)
        qk = service.get('t', str(sk).lower())
        qn = f'rtq_{qk}_queue' if queue_num <=1 else f'rtq_{qk}{i}_queue'
        if not Config.is_prod():
            # 本地 Windows 环境下推送到 Redis 队列
            uuid = Str.uuid()
            task_data = {
                'id': uuid,
                'task_spec': service_name,
                'args': args,
                'kwargs': kwargs,
                'ttl': 7 * 86400,
                'timeout': 3600,
                'create_time': Time.date()
            }
            task_str = Str.parse_json_string_ignore(task_data)
            redis_conn.lpush(qn, task_str)
            redis_conn.expire(qn, task_data['ttl'])
            logger.debug(f"任务提交成功: {qn} - {uuid}","RQT_TASK_SUBMIT")
            return uuid
        else:
            # 生产 Linux 环境下推送到 RQ 队列
            from rq import Queue
            from rq.job import Job
            rq = Queue(qn, connection=redis_conn)
            job: Job = rq.enqueue(
                RedisTaskQueue._execute_task,
                service_name,
                *args,
                **kwargs,
                ttl=7*86400,
                timeout=3600,
                retry_on_ttl=False
            )
            logger.debug(f"任务提交成功: {qn} - {job.id}","RQT_TASK_SUBMIT")
            return job.id

    @staticmethod
    def run_consumer():
        """异步延迟启动消费"""
        queue_list = []
        def queue_worker(queue_name):
            print(f'heartbeat - {queue_name}')
            logger.debug(f'redis task queue starting - {queue_name}', 'RTQ_STA')
            if not Config.is_prod():
                # 本地 Windows 环境下使用 process 消费
                import multiprocessing
                process = multiprocessing.Process(
                    target=RedisTaskQueue.win_consumer,
                    args=(RedisTaskQueue, queue_name,),
                    daemon=True,
                    name=f"process-{queue_name}"
                )
                process.start()
                RedisTaskQueue.PROCESS.append(process)
                return True
            else:
                # 生产 Linux 环境下使用 worker 消费
                from rq import Worker
                if not redis_conn:
                    logger.warning(f'redis connection is empty  - {queue_name}', 'RTQ_WAR')
                    return False
                worker = Worker(
                    queues=[queue_name],
                    name=f"worker-{queue_name}",
                    log_job_description=False
                )
                worker.work(burst=False, with_scheduler=False)
                return True
        for sk, qs in RedisTaskKeys.RTQ_QUEUE_LIST.items():
            qk = qs.get('t', str(sk).lower())
            qnl = [f"rtq_{qk}_queue"] if qs['n'] <=1 else [f"rtq_{qk}{i}_queue" for i in range(1, qs['n'] + 1)]
            queue_list.extend(qnl)
        queue_list = list(set(queue_list))
        for qn in queue_list:
            gevent.sleep(0.1)
            logger.debug(f'redis task queue loading - {qn}', 'RTQ_LOD')
            g = gevent.spawn(queue_worker, qn)  # 为每个队列启动独立 gevent 协程
            RedisTaskQueue.GREENLETS.append(g)
        while len(RedisTaskQueue.GREENLETS) > 0:
            gevent.sleep(3)  # 保持主协程存活
        return True

    @staticmethod
    def stop_consumer():
        """停止队列消费"""
        # process 子协程结束
        [p.terminate() for p in RedisTaskQueue.PROCESS]
        # gevent 子协程结束
        gevent.killall(RedisTaskQueue.GREENLETS, block=False, exception=gevent.GreenletExit, timeout=5)
        RedisTaskQueue.GREENLETS = []
        return True

