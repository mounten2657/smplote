import subprocess
import gevent
import threading
import time
import uuid
import hashlib
import pickle
import inspect
import dis
import docker
from typing import Callable
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from tool.db.cache.redis_client import RedisClient
from tool.core.error import Error
from tool.core.logger import Logger

_timeout = 180  # 超时时间，默认180秒
_executor = ThreadPoolExecutor(max_workers=100, thread_name_prefix="SysTaskExecutor")  # 线程池：控制并发（默认100）
_lock_key = "LOCK_SYS_CNS"  # 并发去重锁
_redis = RedisClient()
logger = Logger()


class Sys:
    """异步任务执行器"""

    GREENLETS = []

    @staticmethod
    def close_sys():
        """关闭本例协程"""
        gevent.killall(Sys.GREENLETS, block=False)
        Sys.GREENLETS = []
        return True

    @staticmethod
    def run_greenlets():
        """保持协程运行"""
        gevent.sleep(0.1)
        #gevent.get_hub().join()
        return True

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
                    logger.debug(f"任务[{task_id}]已在执行，跳过重复执行 - {fn}: {str(ag)[:256]}", 'SYS_TASK_LOCK')
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
        def _delay_wrapper():
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            @Sys._task_lock(task_id, str(func), str(args))
            def _run_task():
                logger.debug(f"任务[{task_id}]正在执行 - {func}: {args}", 'SYS_TASK_RUN')
                return func(*args, **kwargs)
            try:
                future = _executor.submit(_run_task)
                future.result(timeout=timeout)  # 超时控制
            except FutureTimeoutError:
                logger.error(f"任务[{task_id}]执行超时（>{timeout}秒） - {func}: {args}", 'SYS_TASK_TIMEOUT')
            except Exception as e:
                err = Error.handle_exception_info(e)
                logger.error(f"任务[{task_id}]执行失败: {func}: {args} - {err}", 'SYS_TASK_ERROR')
        # 启动延迟线程（立即返回）
        # gevent / threading 只有一个进程 - 会生成多个协程 - 所有协程共享内存 - 伪并发
        threading.Thread(target=_delay_wrapper, daemon=True).start()
        # 由于 gevent 需要先 spawn 再 join 或 sleep 才能真正执行，用起来太麻烦，故舍弃
        # g = gevent.spawn(_delay_wrapper)
        # Sys.GREENLETS.append(g)
        # Sys.run_greenlets()
        return task_id

    @staticmethod
    def shutdown():
        """程序退出时关闭线程池"""
        _executor.shutdown(wait=False)
        Sys.close_sys()

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
    def chmod(dir_path, mod=755):
        """更新目录权限"""
        return Sys.run_command(f'sudo chmod -R {mod} {dir_path}')

    @staticmethod
    def chown(dir_path, own='www:www'):
        """更新目录所有者"""
        return Sys.run_command(f'sudo chown -R {own} {dir_path}')

    @staticmethod
    def mkdir(dir_path, is_sudo=False):
        """创建文件夹"""
        sudo = "sudo" if is_sudo else ""
        return Sys.run_command(f'{sudo} mkdir -p {dir_path}')

    @staticmethod
    def rm_dir(dir_path, is_sudo=False):
        """删除目录或文件"""
        sudo = "sudo" if is_sudo else ""
        return Sys.run_command(f'{sudo} rm -rf {dir_path}') if len(dir_path) > 10 else False

    @staticmethod
    def cp_dir(src_dir, dst_dir, is_sudo=False):
        """复制目录或文件"""
        sudo = "sudo" if is_sudo else ""
        return Sys.run_command(f'{sudo} cp -af {src_dir} {dst_dir}')

    @staticmethod
    def get_docker_container(container_name):
        """获取宿主机 docker 容器对象"""
        try:
            client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            return client.containers.get(container_name)
        except Exception:
            Error.throw_exception(f"获取 docker 容器失败 - {container_name}")
            return None

    @staticmethod
    def delay_kill_gu():
        """终止gu """
        logger.warning(f"正在停止GUNICORN", 'SYS_KGU')
        container = Sys.get_docker_container('www-python')
        return container.stop()

    @staticmethod
    def delay_reload_gu(is_force=0):
        """重载gu """
        logger.warning(f"正在重启GUNICORN - {is_force}", 'SYS_RGU')
        container = Sys.get_docker_container('www-python')
        return container.restart()

    @staticmethod
    def delay_reload_vp():
        """重载vp """
        logger.warning(f"正在重启WECHATPAD", 'SYS_RVP')
        container = Sys.get_docker_container('wechatpad')
        return container.restart()
