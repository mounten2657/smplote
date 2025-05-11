from tool.router.base_app import BaseApp
from tool.core import *
from utils.grpc.open_nat.open_nat_client import OpenNatClient


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
        """检查常规配置"""
        res = {
            "ai": Config.ai_config(),
            "app": Config.app_config(),
            "db": Config.db_config(),
            "logger": Config.logger_config(),
            "wx": Config.wx_config(),
        }
        return self.success(res)

    def init_vps_config(self):
        """初始化vps上的配置文件 - 加密处理"""
        res = OpenNatClient.init_config_qy()
        return self.success(res)

