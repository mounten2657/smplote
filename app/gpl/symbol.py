from tool.router.base_app import BaseApp
from service.gpl.gpl_update_service import GPLUpdateService


class Symbol(BaseApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.gpl = GPLUpdateService()

    def info(self):
        """查询股票基础信息"""
        code = self.params.get('code', '')
        res = self.gpl.formatter.get_stock(code)
        return self.success(res)
