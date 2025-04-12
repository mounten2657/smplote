from typing import Optional, Dict
from openai import OpenAI
from tool.core import *


class AIClientManager:
    """管理不同AI服务的客户端连接"""

    def __init__(self):
        self.config = self._load_config()
        self.clients = {}
        self._init_clients()

    @staticmethod
    def _load_config() -> Dict:
        """加载配置文件"""
        return Config.ai_config()

    def _init_clients(self):
        """初始化所有AI服务客户端"""
        for service, cfg in self.config['services'].items():
            if cfg['api_key']:
                self.clients[service] = OpenAI(
                    api_key=cfg['api_key'],
                    base_url=cfg['base_url'].rstrip('/') + cfg['api_uri']
                )

    def get_client(self, service: Optional[str] = None) -> OpenAI:
        """获取指定服务的客户端"""
        service = service or self.config['last_service']
        return self.clients.get(service)

