from tool.router.base_app_wx import BaseAppWx
from tool.core import Config, Time
from service.vps.open_nat_service import OpenNatService
from service.gpl.gpl_formatter_service import GplFormatterService


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

    def get_stock(self):
        """检查获取股票基本信息是否通畅"""
        code = self.params.get('code', '300126')
        formatter = GplFormatterService()
        res = formatter.get_stock_info(code)
        return self.success(res)

    def get_daily(self):
        """检查获取日线行情信息是否通畅"""
        code = self.params.get('code', '300126')
        sd = self.params.get('sd', Time.dft(Time.now() - 5 * 86400, '%Y-%m-%d'))
        ed = self.params.get('ed', Time.date('%Y-%m-%d'))
        fq = self.params.get('fq', 'qfq')
        formatter = GplFormatterService()
        res = formatter.em.get_daily_quote(code, sd, ed, fq)
        return self.success(res)
