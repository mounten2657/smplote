import time
from tool.router.base_app import BaseApp
from tool.core.config import Config
from tool.unit.wechat.export_wechat_info import ExportWechatInfo


class Index(BaseApp):

    def index(self, **kwargs):
        """首页入口"""
        current_timestamp = int(time.time())
        # self.logger.info({"user_name":"test123"})
        config = Config.app_config()
        response = {
            "__doc__": "hello wechat tool",
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

    def daily_task(self):
        """每日自动化任务入口"""
        all_params = {
            "wxid": self.wxid,
            "g_wxid": self.g_wxid,
            "g_wxid_dir": self.g_wxid_dir,
            "db_config": self.db_config,
            "params": self.params,
        }
        res = ExportWechatInfo.daily_task(all_params)
        return self.success(res)
