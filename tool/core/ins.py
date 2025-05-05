import time
import hashlib
import threading
from functools import wraps
from tool.db.cache.redis_client import RedisClient


class Ins:

    @staticmethod
    def singleton(cls):
        """单例模式装饰器"""
        instances = {}

        @wraps(cls)
        def get_instance(*args, **kwargs):
            def arg_to_str(arg):
                if hasattr(arg, "__str__"):
                    return str(arg)
                return arg.__class__.__name__
            key = f"{cls.__name__}"
            if getattr(cls, 'ARGS_UNIQUE_KEY', False):
                args_str = ''.join(map(arg_to_str, args))
                kwargs_str = ''.join([f"{k}{arg_to_str(v)}" for k, v in sorted(kwargs.items())])
                all_args_str = args_str + kwargs_str
                md5 = hashlib.md5()
                md5.update(all_args_str.encode('utf-8'))
                md5_key = md5.hexdigest()
                key = f"{cls.__name__}_{md5_key}"
            if key not in instances:
                instances[key] = cls(*args, **kwargs)
            return instances[key]

        return get_instance

    @staticmethod
    def synchronized(lock_name):
        """线程同步装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                # 使用 redis 分布式锁
                lock = RedisClient().client.lock(f'ts_lock_{lock_name}', timeout=10)
                with lock:
                    return func(self, *args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def timeout(seconds):
        """线程超时装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                result = None

                def worker():
                    nonlocal result
                    result = func(self, *args, **kwargs)

                t = threading.Thread(target=worker)
                t.start()
                t.join(timeout=seconds)
                if t.is_alive():
                    raise TimeoutError(f"Timeout after {seconds} seconds")
                self.last_exec_time = time.time()
                return result
            return wrapper
        return decorator

