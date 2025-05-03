import time
from tool.router.base_app import BaseApp
from tool.core import *


class Index(BaseApp):

    def index(self, **kwargs):
        """首页入口"""
        current_timestamp = int(time.time())
        # self.logger.info({"user_name":"test123"})
        config = Config.app_config()
        response = {
            "__doc__": "Hello, Smplote tool",
            "timestamp": current_timestamp,
            "version": config.get('SYS_VERSION'),
            "params": self.params,
            "wxid": self.wxid,
            "args": kwargs
        }
        return self.success(response)

    def check_config(self):
        res = {
            "ai": Config.ai_config(),
            "app": Config.app_config(),
            "db": Config.db_config(),
            "logger": Config.logger_config(),
            "wx": Config.wx_config(),
        }
        return self.success(res)
