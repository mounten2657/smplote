import subprocess
import threading
import asyncio
import time
import uuid
from typing import Callable, Dict, Any

# 任务存储：任务ID -> 任务状态/结果
_task_registry: Dict[str, Dict[str, Any]] = {}


class Sys:

    def __init__(self):
        # 创建独立线程运行事件循环
        self._loop = asyncio.new_event_loop()
        self._loop_thread = None
        self._running = False
        self._start_loop()

    def _start_loop(self):
        """在独立线程中启动事件循环"""
        def loop_worker():
            self._running = True
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
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
        if not self._running:
            return False
        try:
            asyncio.run_coroutine_threadsafe(_execute_delayed(), self._loop)
        except Exception as e:
            raise RuntimeError(f'提交延迟任务失败 - {e}')

    def stop_loop(self):
        """停止事件循环和工作线程"""
        if self._loop and self._running:
            self._running = False
            # 安全关闭事件循环
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop_thread.join(timeout=1.0)
            self._loop.close()

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
        task_id = str(uuid.uuid4())

        def _wrapped_task():
            # 更新任务状态为运行中
            _task_registry[task_id] = {
                "status": "running",
                "start_time": time.time(),
            }
            try:
                # 执行目标函数
                result = func(*args, **kwargs)
                # 更新任务结果
                _task_registry[task_id].update({
                    "status": "completed",
                    "end_time": time.time(),
                    "result": result
                })
            except Exception as e:
                # 记录异常信息
                _task_registry[task_id].update({
                    "status": "error",
                    "end_time": time.time(),
                    "error": str(e)
                })

        # 启动守护线程执行任务
        Sys()._delayed_exec(delay_seconds, _wrapped_task)
        return task_id

    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        return _task_registry.get(task_id, {"status": "not_found"})

    @staticmethod
    def delay_git_pull():
        """延迟三秒后，拉取最新代码，并重启 flask """
        def pull_code():
            Sys.run_command('sudo /opt/shell/init/reload_flask.sh >>/tmp/reload_flask.log 2>&1')
        return Sys.delayed_task(5, pull_code)


