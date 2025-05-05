import redis
from typing import Dict, Any
from tool.core.config import Config


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
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        """
        初始化连接池（通过装饰器保证单例）
        """
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

