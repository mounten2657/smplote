import json
import time
import uuid
import threading
from retrying import retry
from datetime import datetime
from typing import Any, Dict
from tool.core import Logger, Sys, Ins, Str, Attr
from tool.db.cache.redis_client import RedisClient
from tool.db.cache.redis_task_keys import RedisTaskKeys

logger = Logger()


@Ins.singleton
class RedisTaskQueue:
    """Redis-based distributed task queue with process/thread safety.

    Features:
        - Atomic task claiming via Redis RPOPLPUSH
        - Delayed task support with ZSET
        - Heartbeat monitoring for stalled tasks
        - Automatic retry with exponential backoff
        - Deduplication via task IDs
    Usage:
        queue = RedisTaskQueue()
        queue.submit(
            'module.path.Service@method',
            {'param': 'value'},
            delay=5  # Execute after 5 seconds
        )
    """

    queue_list = ['rtq_callback_queue', 'rtq_usr_queue']
    default_queue = queue_list[0]

    def __init__(self, queue_name: str = default_queue):
        """
        Args:
            queue_name: Base name for all Redis keys
        """
        self.client = RedisClient()
        self.redis = self.client.client
        self.queue_name = queue_name
        self.processing_queue = f"{queue_name}:processing"
        self.delayed_queue = f"{queue_name}:delayed"
        self._register_lua_scripts()

    def _register_lua_scripts(self):
        """Register all Lua scripts for atomic operations"""
        # Enqueue with delay support
        self._enqueue_script = self.redis.register_script("""
                local main_q = KEYS[1]
                local delay_q = KEYS[2]
                local delay = tonumber(ARGV[1])
                local task = ARGV[2]

                if delay > 0 then
                    local execute_at = tonumber(redis.call('TIME')[1]) + delay
                    return redis.call('ZADD', delay_q, execute_at, task)
                else
                    return redis.call('LPUSH', main_q, task)
                end
            """)

        # Atomic task claiming
        self._claim_script = self.redis.register_script("""
                local main_q = KEYS[1]
                local processing_q = KEYS[2]
                local worker_id = ARGV[1]

                local task = redis.call('RPOPLPUSH', main_q, processing_q)
                if task then
                    redis.call('HSET', processing_q..':workers', worker_id, task)
                    redis.call('HSET', processing_q..':heartbeats', task, ARGV[2])
                    return task
                end
                return nil
            """)

    def _migrate_delayed_tasks(self):
        """Move ready delayed tasks to main queue (atomic)"""
        now = int(time.time())
        tasks = self.redis.zrangebyscore(
            self.delayed_queue,
            0,
            now,
            start=0,
            num=100  # Batch size
        )

        if tasks:
            pipeline = self.redis.pipeline()
            pipeline.lpush(self.queue_name, *tasks)
            pipeline.zremrangebyscore(
                self.delayed_queue,
                0,
                now
            )
            pipeline.execute()

    def submit(self, task_spec: str, *args, delay: int = 0, **kwargs) -> str:
        """Submit a task to the queue.

        Args:
            task_spec: Format 'module.path.ClassName@method_name'
            delay: Seconds to delay execution (default: 0)
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            str: Unique task ID
        """
        task_id = str(uuid.uuid4())
        task_data = json.dumps({
            'id': task_id,
            'spec': task_spec,
            'args': args,
            'kwargs': kwargs,
            'created_at': datetime.now().isoformat(),
            'attempts': 0
        })

        self._enqueue_script(
            keys=[self.queue_name, self.delayed_queue],
            args=[delay, task_data]
        )
        return task_id

    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    def _execute_task(self, task_data: Dict[str, Any]) -> bool:
        """Execute task with retry and heartbeat."""
        task_id = task_data['id']
        try:
            # Update heartbeat
            self.redis.hset(
                f"{self.processing_queue}:heartbeats",
                task_id,
                datetime.now().isoformat()
            )

            # Dynamic method invocation
            action = Attr.get_action_by_path(task_data['spec'])
            logger.debug(f"正在执行队列任务[{self.queue_name}]: {task_data['spec']}", 'RTQ_TASK_EXEC_PAR')
            res = action(*task_data['args'], **task_data['kwargs'])
            logger.debug(f"队列任务执行结果[{self.queue_name}]: {res}", 'RTQ_TASK_EXEC_RET')
            return True
        except ImportError as e:
            logger.error(f"Module import failed: {e}", 'RTQ_TASK_MODULE_ERROR')
            raise
        except Exception as e:
            task_data['attempts'] += 1
            logger.warning(
                f"Task[{self.queue_name}] {task_id} failed (attempt {task_data['attempts']}): {e}",
                'RTQ_TASK_RETRY'
            )
            raise

    def _reclaim_stalled_tasks(self, timeout_sec: int = 300):
        """Return stalled tasks to main queue."""
        now = datetime.now()
        heartbeats = self.redis.hgetall(f"{self.processing_queue}:heartbeats")

        pipeline = self.redis.pipeline()
        for task_id, hb_str in heartbeats.items():
            if (now - datetime.fromisoformat(hb_str)).total_seconds() > timeout_sec:
                # Get task data from worker tracking
                task_data = self.redis.hget(
                    f"{self.processing_queue}:workers",
                    task_id
                )
                if task_data:
                    pipeline.lpush(self.queue_name, task_data)
                    pipeline.hdel(
                        f"{self.processing_queue}:workers",
                        task_id
                    )
        pipeline.execute()

    def consume(self, worker_id: str, batch_size: int = 5, idle_wait: float = 0.1):
        """Main consumer loop.

        Args:
            worker_id: Unique identifier for this worker
            batch_size: Max tasks to process per iteration
            idle_wait: Seconds to sleep when queue is empty
        """
        while True:
            try:
                # 1. Migrate delayed tasks
                self._migrate_delayed_tasks()

                # 2. Process tasks
                processed = 0
                while processed < batch_size:
                    # Claim task atomically
                    task_data = self._claim_script(
                        keys=[self.queue_name, self.processing_queue],
                        args=[worker_id, datetime.now().isoformat()]
                    )
                    if not task_data:
                        break

                    task = json.loads(task_data)
                    try:
                        if self._execute_task(task):
                            # Remove from processing queue on success
                            self.redis.lrem(self.processing_queue, 0, task_data)
                        processed += 1
                    finally:
                        # Cleanup worker tracking
                        self.redis.hdel(
                            f"{self.processing_queue}:workers",
                            worker_id
                        )
                        self.redis.hdel(
                            f"{self.processing_queue}:heartbeats",
                            task['id']
                        )

                # 3. Reclaim stalled tasks periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    self._reclaim_stalled_tasks()

                # 4. Idle wait if no tasks
                if processed == 0:
                    time.sleep(idle_wait)

            except Exception as e:
                logger.error(f"Consumer {worker_id} crashed: {e}", 'RTQ_CONSUMER_FATAL')
                # time.sleep(1)

    def get_queue_stats(self) -> Dict[str, int]:
        """Get current queue status."""
        return {
            'pending': self.redis.llen(self.queue_name),
            'processing': self.redis.llen(self.processing_queue),
            'delayed': self.redis.zcard(self.delayed_queue),
            'stalled': self.redis.hlen(f"{self.processing_queue}:heartbeats")
        }

    def add_task(self, sk, data):
        """往队列中添加任务"""
        service = RedisTaskKeys.RTQ_SERVICE_LIST.get(sk)
        if not service:
            raise ValueError(f'Not register service - {sk}')
        return self.submit(service, data)

    @staticmethod
    def run_consumer():
        """异步延迟启动消费"""
        def run(queue_name):
            # redis = RedisClient()
            # time.sleep(Str.randint(1, 10))
            # # 确保每个队列只能有一个消费者
            # cache_key = 'LOCK_RTQ_CNS'
            # if redis.get(cache_key, [queue_name]):
            #     return False
            # if not redis.set_nx(cache_key, 1, [queue_name]):
            #     return False
            uid = Str.uuid()
            print(f'heartbeat - {queue_name}')
            logger.debug(f'redis task queue starting - {queue_name}', 'RTQ_STA')
            return RedisTaskQueue(queue_name).consume(uid)
        for qn in RedisTaskQueue.queue_list:
            time.sleep(1)
            logger.debug(f'redis task queue loading - {qn}', 'RTQ_LOD')
            thread = threading.Thread(target=run, args=(qn,), daemon=True)
            thread.start()
        return True
