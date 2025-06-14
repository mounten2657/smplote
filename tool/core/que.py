import time
import queue
import threading
from multiprocessing import Lock
from tool.core.http import Http
from tool.core.ins import Ins
from tool.core.logger import Logger

logger = Logger()


class Que:

    MAX_QUEUE_SIZE = 9999      # 队列最大长度，超过会直接丢弃

    _lock_name = None          # 使用类名作为线程同步锁名

    def __init__(self):
        self._send_lock = Lock()  # 发送操作锁
        self._queue_lock = Lock()  # 队列操作锁
        self._lock_name = self.__class__.__name__
        self.message_queue = queue.Queue(maxsize=self.MAX_QUEUE_SIZE)
        self.is_processing = False
        self.last_exec_time = 0
        self._start_consumer()

    def _start_consumer(self):
        """使用队列进行消费，不同子类不同锁，互不影响"""
        def consumer():
            while True:
                try:
                    with self._queue_lock:
                        if self.message_queue.empty():
                            self.is_processing = False
                            time.sleep(0.1)
                            continue
                        task = self.message_queue.get_nowait()
                        self.is_processing = True
                    try:
                        logger.debug(f"[{self.__class__.__name__}] Queue Consumer Listening", "QUE_EXC")
                        res = self._execute_with_timeout(task)
                        logger.info(res, 'QUE_RES')
                        time.sleep(0.1)
                    except TimeoutError as e:
                        logger.error(f"[{self.__class__.__name__}] [Timeout] {e}", 'QUE_TIMEOUT')
                except Exception as e:
                    logger.error(f"[{self.__class__.__name__}] Error: {e}", 'QUE_ERR')
                with self._queue_lock:
                    self.message_queue.task_done()

        thread = threading.Thread(target=consumer, daemon=True)
        thread.start()

    @Ins.timeout(30)
    def _execute_with_timeout(self, task):
        """带超时控制的执行方法"""
        return self._que_exec(**task)

    @Ins.synchronized('_send_lock')
    def _que_exec(self, **kwargs):
        """子类必须实现的具体执行方法"""
        err_msg = "Subclasses must implement this method"
        logger.error(err_msg, "QUE_ERR")
        raise NotImplementedError(err_msg)

    @Ins.synchronized('_queue_lock')
    def que_submit(self, **kwargs):
        """提交任务到队列"""
        logger.debug(f"[{self.__class__.__name__}] Queue Process - {kwargs}", "QUE_ENT")
        if self.message_queue.qsize() >= self.MAX_QUEUE_SIZE:
            logger.warning(f"[{self.__class__.__name__}] Queue full, dropped: {kwargs}", "QUE_FULL")
            return False
        self.message_queue.put(kwargs)
        logger.debug(f"[{self.__class__.__name__}] Queued (size: {self.message_queue.qsize()})", "QUE_SUB")
        # 如果是命令行模式，需等待队列处理完成
        if Http.get_request_method() == 'COMMAND':
            while not self.message_queue.empty():
                time.sleep(0.2)
        return True


