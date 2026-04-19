from tool.router.base_app_wx import BaseAppWx
from tool.core import Config, Time
from service.vps.open_nat_service import OpenNatService
from tool.db.cache.redis_task_queue import RedisTaskQueue


class Index(BaseAppWx):

    def index(self):
        """首页入口"""
        response = {
            "timestamp": Time.now(),
            "version": Config.app_config().get('SYS_VERSION'),
            "is_prod": Config.is_prod(),
            "app_key": self.app_key,
            "params": self.params,
        }
        return self.success(response)

    def failed_job(self):
        """获取失败任务"""
        res = RedisTaskQueue.get_failed_job()
        return self.success(res)

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
