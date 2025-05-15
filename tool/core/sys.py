import subprocess
import threading
import time
import uuid
from typing import Callable, Dict, Any

# 任务存储：任务ID -> 任务状态/结果
_task_registry: Dict[str, Dict[str, Any]] = {}


class Sys:

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
        延迟执行指定函数（在线程中异步执行）

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
                # 延迟执行
                time.sleep(delay_seconds)
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
        thread = threading.Thread(target=_wrapped_task, daemon=True)
        thread.start()
        return task_id

    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        return _task_registry.get(task_id, {"status": "not_found"})


