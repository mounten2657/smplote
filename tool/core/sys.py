import subprocess
import threading
import time
import uuid
import hashlib
import pickle
import inspect
import dis
from typing import Callable
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from tool.db.cache.redis_client import RedisClient
from tool.core.error import Error
from tool.core.logger import Logger

_timeout = 120  # 超时时间，默认120秒
_executor = ThreadPoolExecutor(max_workers=100, thread_name_prefix="SysTaskExecutor")  # 线程池：控制并发（默认100）
_lock_key = "LOCK_SYS_CNS"  # 并发去重锁
_redis = RedisClient()
logger = Logger()


class Sys:
    """异步任务执行器"""

    @staticmethod
    def _generate_task_id(func: Callable, *args, **kwargs) -> str:
        """生成任务唯一ID（用于去重）"""
        try:
            # 序列化函数和参数生成哈希
            func_name = func.__name__
            if '<lambda>' == func_name:
                # 特殊处理lambda函数
                bytecode = dis.Bytecode(func)
                bytecode_str = "\n".join(f"{i.opname} {i.argval or ''}" for i in bytecode)
                source = inspect.getsource(func).strip().replace('\n', '')
                func_name = f"lambda|{source}|{bytecode_str}"
            data = pickle.dumps((func_name, args, kwargs))
            return hashlib.sha256(data).hexdigest()
        except Exception:
            # 序列化失败时用随机ID
            return str(uuid.uuid4())

    @staticmethod
    def _task_lock(task_id: str, fn: str, ag: str):
        """分布式锁装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取Redis锁（原子操作）
                acquired = _redis.set_nx(_lock_key, 1, [task_id])
                if not acquired:
                    logger.debug(f"任务[{task_id}]已在执行，跳过重复执行 - {fn}: {ag}", 'SYS_TASK_LOCK')
                    return None  # 其他进程已处理
                try:
                    return func(*args, **kwargs)
                finally:
                    # _redis.delete(_lock_key, [task_id])  # 等自动过期
                    pass
            return wrapper
        return decorator

    @staticmethod
    def delayed_task(func: Callable, *args, **kwargs) -> str:
        """
        延迟执行函数，立即返回task_id

        :param func: 目标函数
        :param args: 函数参数 - p1, p2
        :param kwargs: 函数参数 - p1=11, p2=22
        :return: 任务ID
        """
        # 生成任务ID（去重依据）
        task_id = Sys._generate_task_id(func, *args, **kwargs)
        delay_seconds = kwargs.pop('delay_seconds', 0.1)
        timeout = kwargs.pop('timeout', _timeout)

        # 1. 延迟逻辑：在子线程中先sleep，再提交到线程池
        def _delay_wrapper():
            # 延迟执行
            if delay_seconds > 0:
                time.sleep(delay_seconds)

            # 2. 带锁和超时的任务执行逻辑
            @Sys._task_lock(task_id, str(func), str(args))
            def _run_task():
                # logger.warning(f"任务[{task_id}]正在执行 - {func}: {args}", 'SYS_TASK_RUNNING')
                return func(*args, **kwargs)

            # 3. 提交到线程池并设置超时
            try:
                future = _executor.submit(_run_task)
                future.result(timeout=timeout)  # 超时控制
            except FutureTimeoutError:
                logger.error(f"任务[{task_id}]执行超时（>{timeout}秒） - {func}: {args}", 'SYS_TASK_TIMEOUT')
            except Exception as e:
                err = Error.handle_exception_info(e)
                logger.error(f"任务[{task_id}]执行失败: {func}: {args} - {err}", 'SYS_TASK_ERROR')

        # 启动延迟线程（立即返回）
        threading.Thread(target=_delay_wrapper, daemon=True).start()
        return task_id

    @staticmethod
    def shutdown():
        """程序退出时关闭线程池"""
        _executor.shutdown(wait=False)

    @staticmethod
    def run_command(command):
        result = subprocess.run(
            [
                'bash',
                '-c',
                f'{command}'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    @staticmethod
    def delay_git_pull():
        """延迟三秒后，拉取最新代码，并重启 flask """
        command = 'sudo /opt/shell/init/reload_flask.sh >>/dev/null 2>&1'
        return Sys.delayed_task(Sys.run_command, command, delay_seconds=3)

    @staticmethod
    def delay_kill_gu():
        """终止gu """
        command = 'sudo pkill -9 -f gunicorn'
        return Sys.delayed_task(Sys.run_command, command, delay_seconds=3)

    @staticmethod
    def delay_reload_gu(is_force=0):
        """重载gu """
        command = f'sudo /opt/shell/init/init_flask.sh >>/dev/null 2>&1{' 1' if is_force else ' '}'
        return Sys.delayed_task(Sys.run_command, command, delay_seconds=3)

    @staticmethod
    def delay_kill_vp():
        """终止vp """
        command = 'sudo pkill -9 -f stay'
        return Sys.delayed_task(Sys.run_command, command, delay_seconds=3)

    @staticmethod
    def delay_reload_vp():
        """重载vp """
        command = 'sudo /opt/shell/init/init_wechatpad.sh >>/dev/null 2>&1'
        return Sys.delayed_task(Sys.run_command, command, delay_seconds=3.5)
