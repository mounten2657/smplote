import hashlib
from functools import wraps
from typing import TypeVar, Type, Any
from tool.core.attr import Attr
from tool.core.logger import Logger
from tool.db.cache.redis_client import RedisClient

T = TypeVar('T')
logger = Logger()
redis = RedisClient()


class Ins:

    @staticmethod
    def singleton(cls: Type[T]) -> Type[T]:
        """单例模式装饰器"""
        instances = {}

        @wraps(cls)
        def get_instance(*args: Any, **kwargs: Any) -> T:
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
    def cached(cache_key: str):
        """缓存装饰器"""
        def decorator(method):
            def wrapper(self, *args, **kwargs):
                # 尝试从缓存获取
                if cache := redis.get(cache_key, tuple(args)):
                    return cache
                # 调用原始方法获取数据
                data = method(self, *args, **kwargs)
                if data:
                    save_cache = True
                    # 判断数据是否有效的规则列表
                    rules = [
                        {"key": "code", "val": 0},
                        {"key": "Code", "val": 200},
                    ]
                    for rule in rules:
                        if 1 == Attr.get(data, 'cached'):
                            break
                        if Attr.has_keys(data, rule['key']):
                            if Attr.get(data, rule['key']) != rule['val']:
                                save_cache = False
                                break
                    if save_cache:
                        redis.set(cache_key, data, tuple(args))
                return data
            return wrapper
        return decorator
