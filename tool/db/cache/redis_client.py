import redis
import datetime
from typing import Dict, Any
from tool.db.cache.redis_keys import RedisKeys
from tool.core.config import Config
from tool.core.attr import Attr
from tool.core.str import Str
from tool.core.logger import Logger

logger = Logger()


class RedisClient:
    """
    Redis 连接客户端（单例模式）
    配置从环境变量读取：
      - REDIS_HOST: 主机地址（默认 127.0.0.1）
      - REDIS_PORT: 端口（默认 6379）
      - REDIS_PASSWORD: 密码（必须）
      - REDIS_DB: 数据库编号（默认 0）
      - REDIS_MAX_CONNECTIONS: 连接池大小（默认 50）
    """

    _instance = None
    _pool = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            # cls._instance.__init__()  # new 执行完后会自动调用 init
        return cls._instance

    def __init__(self):
        """
        初始化连接池（通过装饰器保证单例）
        """
        if self._pool is None:
            logger.warning("----Initializing gevent-compatible Redis pool----", 'RD_CONN')
            self._init_pool()

    def _init_pool(self):
        """初始化连接池"""
        config = self._load_config()
        self._pool = redis.ConnectionPool(
            host=config['host'],
            port=config['port'],
            password=config['password'],
            db=config['db'],
            max_connections=config['max_connections'],
            decode_responses=True,  # 自动解码返回字符串
            socket_keepalive=True,  # 保持长连接
            health_check_interval=30,  # 健康检查间隔
            # ssl=False,  # 如需SSL请设置为True
        )

    @staticmethod
    def _load_config() -> Dict[str, Any]:
        return Config.redis_config()

    @property
    def client(self) -> redis.Redis:
        """
        获取Redis连接客户端

        :return: redis.Redis 实例
        :raises: RuntimeError 如果连接未初始化
        """
        if not self._pool:
            raise RuntimeError("Redis连接池未初始化")
        return redis.Redis(connection_pool=self._pool)

    def ping(self) -> bool:
        """测试连接是否可用"""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False

    def close(self):
        """关闭所有连接"""
        if self._pool:
            self._pool.disconnect()

    def __enter__(self):
        """支持上下文管理"""
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时自动关闭连接"""
        self.close()

    def _format_key(self, key_name, args=None):
        """
        获取Redis缓存key信息（键名 + 过期时间）

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: key, ttl
        """
        if key_name not in RedisKeys.CACHE_KEY_STRING:
            raise ValueError(f"未定义缓存键: {key_name}")
        key_info = RedisKeys.CACHE_KEY_STRING[key_name]
        args = args or []  # 默认为空列表
        # 计算key中'%s'的数量
        placeholders_count = key_info["key"].count('%s')
        # 根据占位符数量调整args的长度
        if len(args) > placeholders_count:
            # 如果args元素过多，截取前placeholders_count个元素
            args = args[:placeholders_count]
        elif len(args) < placeholders_count:
            # 如果args元素不足，用 'null' 字符串补齐
            args.extend(['null'] * (placeholders_count - len(args)))
        # 格式化键（如果有参数的话）
        formatted_key = key_info["key"] % tuple(args) if args else key_info["key"]
        ttl = key_info["ttl"]
        if 'today' == ttl:
            ttl = (86400 - datetime.datetime.now().timestamp() % 86400)
        # ttl 必然有值，随机加上一个时间，避免所有缓存在同一时间失效
        ttl = int(ttl)
        if ttl >= 900:
            ttl += Str.randint(1, 300)  # 误差为 5 分钟
        return formatted_key, ttl

    def get(self, key_name, args=None):
        """
        获取Redis缓存值

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: 缓存值（如果是JSON字符串会自动解析为对象）
        """
        formatted_key, ttl = self._format_key(key_name, args)
        value = self.client.get(formatted_key)
        if value is None:
            return None
        return Attr.parse_json_ignore(value)

    def set(self, key_name, value, args=None):
        """
        设置Redis缓存值 - setex

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: value: 要缓存的值（如果是对象会自动转为JSON字符串）
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: Redis操作结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        # 尝试将值序列化为JSON
        value = Str.parse_json_string_ignore(value)
        return self.client.setex(formatted_key, ttl, value)

    def set_nx(self, key_name, value, args=None):
        """
        设置Redis缓存值 - setnx

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: value: 要缓存的值（如果是对象会自动转为JSON字符串）
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: Redis操作结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        # 尝试将值序列化为JSON
        value = Str.parse_json_string_ignore(value)
        res = self.client.setnx(formatted_key, value)
        self.client.expire(formatted_key, int(ttl))
        return res

    def incr(self, key_name, args=None, amount=1):
        """
        Redis缓存值自增

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: amount: 自增步长，默认1
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: Redis操作结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        res = self.client.incrby(formatted_key, amount)
        self.client.expire(formatted_key, int(ttl))
        return res

    def decr(self, key_name, args=None, amount=1):
        """
        Redis缓存值自减

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: amount: 自减步长，默认1
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: Redis操作结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        res = self.client.decrby(formatted_key, amount)
        self.client.expire(formatted_key, int(ttl))
        return res

    def l_len(self, key_name, args=None):
        """
        获取列表长度

        :param: key_name: 缓存键名称（如"XXX_LIST"）
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: 列表长度
        """
        formatted_key, ttl = self._format_key(key_name, args)
        list_len = self.client.llen(formatted_key)
        return list_len or 0

    def l_push(self, key_name, d_list=None, args=None):
        """
        往列表中插入数据 - 左进

        :param: key_name: 缓存键名称（如"XXX_LIST"）
        :param: d_list: 数据列表
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: Redis 操作结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        res = self.client.lpush(formatted_key, *d_list)
        print(ttl)
        self.client.expire(formatted_key, int(ttl))
        return res

    def r_pop(self, key_name, count=1, args=None):
        """
        从列表中弹出元素 - 右出

        :param: key_name: 缓存键名称（如"XXX_LIST"）
        :param: count: 弹出个数，默认一个
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: Redis 操作结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        res = self.client.rpop(formatted_key, count)
        return res

    def delete(self, key_name, args=None):
        """
        删除Redis缓存值

        :param: key_name: 缓存键名称（如"VP_USER_INFO"）
        :param: args: 格式化键所需的参数列表（可为None或空列表）
        :return: 删除结果
        """
        formatted_key, ttl = self._format_key(key_name, args)
        if '*' in formatted_key:
            formatted_key = self.client.keys(formatted_key)
            if len(formatted_key):
                return self.client.delete(*formatted_key)
            else:
                return False
        return self.client.delete(formatted_key)
