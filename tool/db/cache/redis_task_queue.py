import multiprocessing
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
    PROCESS = []

    def _queue_worker(self, queue_name):
        """队列消费工作"""
        print(f'heartbeat - {queue_name}')
        logger.debug(f'redis task queue starting - {queue_name}', 'RTQ_STA')
        if not Config.is_prod():
            # 本地 Windows 环境下直接 while True 消费
            try:
                while True:
                    Time.sleep(1)
                    res = redis_conn.blpop(queue_name, timeout=3)
                    if not res:
                        continue
                    _, task_str = res
                    task_data = Attr.parse_json_ignore(task_str)
                    task_spec = task_data['spec']
                    args = task_data['args']
                    kwargs = task_data['kwargs']
                    RedisTaskQueue._execute_task(self, task_spec, *args, **kwargs)
            except KeyboardInterrupt:
                logger.debug('redis task queue canceled', 'RTQ_CAL')
            return True
        else:
            # 生产 Linux 环境下使用 worker 消费
            from rq import Worker
            if not redis_conn:
                logger.warning(f'redis connection is empty  - {queue_name}', 'RTQ_WAR')
                return False
            worker = Worker(
                queues=[queue_name],
                connection=redis_conn,
                log_job_description=False
            )
            worker.work(burst=False, with_scheduler=False, logging_level='WARNING')
            return True

    def _execute_task(self, task_spec: str, *args, **kwargs) -> bool:
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
    def get_queue_list(sk: str='') -> str | list[str]:
        """获取队列名列表 - 支持单个"""
        queue_list = []
        for sn, qs in RedisTaskKeys.RTQ_QUEUE_LIST.items():
            sn = str(sn).lower()
            qk = qs.get('t', sn)
            qnl = [f"rtq_{qk}_queue"] if qs['n'] <=1 else [f"rtq_{qk}{i}_queue" for i in range(1, qs['n'] + 1)]
            if sk.lower() == sn:  # 单个获取
                if not RedisTaskKeys.RTQ_QUEUE_LIST.get(sk):
                    raise ValueError(f'Not register service - {sk}')
                return Attr.random_choice(qnl)
            queue_list.extend(qnl)
        queue_list = list(set(queue_list))
        return queue_list

    @staticmethod
    def add_task(sk, *args, **kwargs):
        """往队列中添加任务"""
        service = RedisTaskKeys.RTQ_QUEUE_LIST.get(sk)
        service_name = service.get('s')
        qn = RedisTaskQueue.get_queue_list(sk)
        if not Config.is_prod():
            # 本地 Windows 环境下推送到 Redis 队列
            uuid = Str.uuid()
            task_data = {
                'id': uuid,
                'spec': service_name,
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
            queue = Queue(qn, connection=redis_conn)
            job = queue.enqueue(
                RedisTaskQueue._execute_task,
                args=(RedisTaskQueue, service_name, *args,),
                kwargs=kwargs,
                ttl=3600,  # 任务排队入队列的最大时间
                result_ttl=3600,  # 任务结果保存时间
                failure_ttl=80400,  # 失败结果保存时间
                job_timeout=3 * 86400,  # 任务的最大运行时间
                retry=0  # 不重试
            )
            logger.debug(f"任务提交成功: {qn} - {job.id}","RQT_TASK_SUBMIT")
            return job.id

    @staticmethod
    def get_failed_job(is_clear=0):
        """获取失败任务"""
        if not Config.is_prod():
            return []
        from rq import Queue
        failed_job_list = []
        queue_list = RedisTaskQueue.get_queue_list()
        for qn in queue_list:
            queue = Queue(qn, connection=redis_conn)
            failed_registry = queue.failed_job_registry
            if is_clear:
                expire_time = Time.now() + 365 * 86400
                failed_registry.cleanup(expire_time)  # 删除 failed
                queue.finished_job_registry.cleanup(expire_time)  # 删除 finished
                # queue.delete(delete_jobs=True)
                logger.warning(f'队列清除完毕 - {qn}', 'RQT_TASK_WAR')
                continue
            job_id_list = failed_registry.get_job_ids()
            for job_id in job_id_list:
                job = queue.fetch_job(job_id)
                fail = {
                    "id": job_id,
                    "des": str(job.description),
                    "res": str(job.latest_result().exc_string),
                    "meta": str(job.meta),
                    "time": str(job.started_at)
                }
                failed_job_list.append(fail)
        return failed_job_list

    @staticmethod
    def run_consumer():
        """异步延迟启动消费"""
        ctx = multiprocessing.get_context('spawn')
        queue_list = RedisTaskQueue.get_queue_list()
        cors = []  # multiprocessing 会生成多个进程 - 每个进程独立内存且不共享 - 真正的并发
        for qn in queue_list:
            Time.sleep(Str.randint(5, 10) / 10)
            if not redis.set_nx('LOCK_RTQ_CNS', 1, [qn]):
                logger.debug(f'redis task queue repeat - skip - {qn}', 'RTQ_SKP')
                return False
            logger.debug(f'redis task queue loading - {qn}', 'RTQ_LOD')
            process = ctx.Process(
                target=RedisTaskQueue._queue_worker,
                args=(RedisTaskQueue, qn,),
                daemon=False
            )
            process.start()
            cors.append(process)
        RedisTaskQueue.PROCESS.extend(cors)
        return True

    @staticmethod
    def stop_consumer():
        """停止队列消费"""
        # process 子协程结束
        [p.terminate() for p in RedisTaskQueue.PROCESS]
        RedisTaskQueue.PROCESS = []
        return True

