from tool.router.base_app_wx import BaseAppWx
from tool.core import Config, Time
from service.vps.open_nat_service import OpenNatService


class Index(BaseAppWx):

    def index(self):
        """首页入口"""
        current_timestamp = Time.now()
        response = {
            "__doc__": "Hello SMP",
            "timestamp": current_timestamp,
            "version": Config.app_config().get('SYS_VERSION'),
            "params": self.params,
            "is_prod": Config.is_prod(),
            "app_key": self.app_key,
        }
        return self.success(response)

    def check_config(self):
        """检查常规配置"""
        res = {
            "app": Config.app_config(),
            "logger": Config.logger_config(),
            "wx": Config.wx_config(),
        }
        return self.success(res)

    def init_vps_config(self):
        """初始化vps上的配置文件 - 加密处理"""
        res = OpenNatService.init_vps_config_qy()
        return self.success(res)

