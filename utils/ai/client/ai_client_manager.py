import openai
from typing import Optional, Dict
from openai import OpenAI
from tool.core import Logger, Config, Error, Http

logger = Logger()


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
        """初始化AI服务客户端"""
        last_service = self.config['last_service']
        for service, cfg in self.config['services'].items():
            if last_service == service and cfg['api_key']:
                self.clients[service] = OpenAI(
                    api_key=cfg['api_key'],
                    base_url=cfg['base_url'].rstrip('/') + cfg['api_uri']
                )

    def get_client(self, service: Optional[str] = None) -> OpenAI:
        """获取指定服务的客户端"""
        service = service or self.config['last_service']
        return self.clients.get(service)

    def call_ai(self, messages: list, service: Optional[str] = '') -> str:
        """
        调用AI接口
        :param messages:  对话列表 -  [{"role": "system", "content": prompt_text}, {"role": "user", "content": content}]
        :param service:  AI 服务商
        :return:
        """
        service = service if service else self.config['last_service']  # 获取默认服务商
        logger.info({"service": service,"content": str(messages)[0:100]}, 'CALL_AI_TXT', 'ai')
        try:
            client = self.clients.get(service)
            response = client.chat.completions.create(
                model=self.config['services'][service or self.config['last_service']]['model'],
                messages=messages,
                temperature=0.3
            )
            res = response.choices[0].message.content
            logger.info({"service": service, "content": res}, 'CALL_AI_RES', 'ai')
        except (Exception, openai.InternalServerError) as e:
            res = Error.handle_exception_info(e)
            logger.info({"service": service, "content": res}, 'CALL_AI_EXP', 'ai')
        return res

    def call_ai_web(self, content, service, extra=None):
        """调用web形式的api"""
        extra = extra if extra else {}
        rid = extra.get('rid', '')
        logger.info({"service": service,"content": str(content)[0:100]}, 'CALL_AI_WEB_TXT', 'ai')
        try:
            cfg = self.config['services'][service]
            api_key = cfg['api_key']
            base_url = cfg['base_url'].rstrip('/') + cfg['api_uri']
            params = {"key": api_key, "msg": content, "rm": rid}
            res = Http.send_request('GET', base_url, params)
            logger.info({"service": service, "content": res}, 'CALL_AI_WEB_RES', 'ai')
        except Exception as e:
            res = Error.handle_exception_info(e)
            logger.info({"service": service, "content": res}, 'CALL_AI_WEB_EXP', 'ai')
        return res
