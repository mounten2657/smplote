import subprocess
import threading
import asyncio
import time
import uuid
import hashlib
import pickle
import inspect
import dis
from typing import Callable, Dict, Any
from functools import wraps
from tool.db.cache.redis_client import RedisClient
from tool.core.logger import Logger

# 任务存储：任务ID -> 任务状态/结果
_task_registry: Dict[str, Dict[str, Any]] = {}
_lock_key = "LOCK_SYS_CNS"
_redis = RedisClient()
logger = Logger()


class Sys:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                self._loop = None
                self._loop_thread = None
                self._process_id = str(id(self))
                self._initialized = True

    def _start_loop(self):
        """在独立线程中启动事件循环"""
        def loop_worker():
            if not self._loop:
                self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        with self._lock:
            if self._loop and self._loop.is_running():
                logger.debug("Event loop already running", 'SYS_TSK_LOP')
                return False
            self._loop_thread = threading.Thread(target=loop_worker, daemon=True)
            self._loop_thread.start()

    def _delayed_exec(self, delay_seconds: float, func: Callable, *args, **kwargs):
        """
        异步延迟执行任务
        参数:
            delay_seconds: 延迟执行的秒数
            func: 要执行的函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
        """
        # 创建异步任务
        async def _execute_delayed():
            await asyncio.sleep(delay_seconds)
            # 执行函数（异步中调用同步函数需注意）
            if asyncio.iscoroutinefunction(func):
                await func(*args, **kwargs)
            else:
                func(*args, **kwargs)
        # 安全地将任务提交到事件循环
        logger.debug('delay task executing', 'SYS_TSK_STA')
        if not self._loop or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            if not self._loop_thread or not self._loop_thread.is_alive():
                self._start_loop()
        try:
            asyncio.run_coroutine_threadsafe(_execute_delayed(), self._loop)
        except Exception as e:
            msg = f'提交延迟任务失败 - {e}'
            logger.error(msg, 'SYS_TSK_ERR')
            return False

    def stop_loop(self):
        """停止事件循环和工作线程"""
        if self._loop:
            # 安全关闭事件循环
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop_thread.join(timeout=1.0)
            self._loop.close()

    @staticmethod
    def _task_lock(task_id: str):
        """分布式锁装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 获取Redis锁（原子操作）
                acquired = _redis.set_nx(_lock_key, 1, [task_id])
                if not acquired:
                    return None  # 其他进程已处理
                try:
                    return func(*args, **kwargs)
                finally:
                    # _redis.delete(_lock_key, [task_id])  # 等自动过期
                    pass
            return wrapper
        return decorator

    @staticmethod
    def _generate_task_id(func: Callable, *args, **kwargs) -> str:
        """生成基于任务内容的唯一指纹"""
        try:
            func_name = Sys._get_func_name(func)
            # 序列化函数名和参数
            data = pickle.dumps((func_name, args, kwargs))
            # 计算哈希值
            return hashlib.sha256(data).hexdigest()
        except Exception as e:
            # 序列化失败时回退到随机ID
            return str(uuid.uuid4())

    @staticmethod
    def _get_func_name(func: Callable):
        """获取唯一的函数名"""
        func_name = func.__name__
        if '<lambda>' == func_name:
            # 获取lambda的字节码
            bytecode = dis.Bytecode(func)
            bytecode_str = "\n".join(
                f"{instr.opname} {instr.argval if instr.argval else ''}"
                for instr in bytecode
            )
            source_line = inspect.getsource(func).strip()
            func_name = f"{source_line}|{bytecode_str}"
            func_name = func_name.replace('\r', '').replace('\n', '').strip()
        return func_name

    @staticmethod
    def delayed_task(delay_seconds: float, func: Callable, *args, **kwargs) -> str:
        """
        延迟执行指定函数（asyncio实现）

        参数:
            delay_seconds: 延迟秒数
            func: 要执行的函数（闭包）
            *args, **kwargs: 传递给函数的参数

            example:
            # 3秒后执行 say_hello 函数
            def say_hello(key): ...
            task_id = Sys.delayed_task(3, say_hello, "World")
            status = Sys.get_task_status(task_id)

        返回:
            任务ID，可用于查询任务状态
        """
        task_id = Sys._generate_task_id(func, args, kwargs)
        func_name = Sys._get_func_name(func)

        @Sys._task_lock(task_id)
        def _wrapped_task():
            # 更新任务状态为运行中
            _task_registry[task_id] = {
                "status": "running",
                "start_time": time.time(),
                "func": func_name,
                "args": str(args),
                "kwargs": str(kwargs)
            }
            _redis.set(_lock_key, _task_registry[task_id], [task_id])
            try:
                # 执行目标函数
                result = func(*args, **kwargs)
                # 更新任务结果
                _task_registry[task_id].update({
                    "status": "completed",
                    "end_time": time.time(),
                    "result": result
                })
                _redis.set(_lock_key, _task_registry[task_id], [task_id])
            except Exception as e:
                # 记录异常信息
                _task_registry[task_id].update({
                    "status": "error",
                    "end_time": time.time(),
                    "error": str(e)
                })
                _redis.set(_lock_key, _task_registry[task_id], [task_id])

        # 启动守护线程执行任务
        Sys()._delayed_exec(delay_seconds, _wrapped_task)
        return task_id

    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        cache = _redis.get(_lock_key, [task_id])
        return cache if cache else {"status": "not_found"}

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
        def pull_code():
            Sys.run_command('sudo /opt/shell/init/reload_flask.sh >>/tmp/reload_flask.log 2>&1')
        return Sys.delayed_task(3, pull_code)

    @staticmethod
    def delay_kill_gu():
        """终止gu """
        return Sys.delayed_task(3, lambda: Sys.run_command('sudo pkill -9 -f gunicorn'))

    @staticmethod
    def delay_reload_gu(is_force=0):
        """重载gu """
        is_force = ' 1' if is_force else ' '
        command = f'sudo /opt/shell/init/init_flask.sh >>/tmp/init_flask.log 2>&1{is_force}'
        return Sys.delayed_task(3, lambda: Sys.run_command(command))

    @staticmethod
    def delay_kill_vp():
        """终止vp """
        return Sys.delayed_task(3, lambda: Sys.run_command('sudo pkill -9 -f stay'))

    @staticmethod
    def delay_reload_vp():
        """重载vp """
        def _exec():
            Sys.run_command('sudo /opt/shell/init/init_wechatpad.sh >>/tmp/init_wechatpad.log 2>&1')
        return Sys.delayed_task(3, _exec)
