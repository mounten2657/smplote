from tool.router.base_app import BaseApp
from tool.core import *


class Index(BaseApp):

    def index(self, **kwargs):
        """首页入口"""
        current_timestamp = Time.now()
        response = {
            "__doc__": "Hello, Smplote tool",
            "timestamp": current_timestamp,
            "version": Config.app_config().get('SYS_VERSION'),
            "params": self.params,
            "is_prod": Config.is_prod(),
            "wxid": self.wxid,
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
