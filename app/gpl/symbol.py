from tool.router.base_app import BaseApp
from tool.core import Time
from service.gpl.gpl_formatter_service import GplFormatterService


class Symbol(BaseApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.formatter = GplFormatterService()

    def info(self):
        """检查获取股票基本信息是否通畅"""
        code = self.params.get('code', '300126')
        res = self.formatter.get_stock_info(code)
        return self.success(res)

    def daily(self):
        """检查获取日线行情信息是否通畅"""
        code = self.params.get('code', '300126')
        sd = self.params.get('sd', Time.dft(Time.now() - 5 * 86400, '%Y-%m-%d'))
        ed = self.params.get('ed', Time.date('%Y-%m-%d'))
        fq = self.params.get('fq', 'qfq')
        res = self.formatter.em.get_daily_quote(code, sd, ed, fq)
        return self.success(res)
