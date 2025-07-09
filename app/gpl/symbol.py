from tool.router.base_app import BaseApp
from service.gpl.gpl_update_service import GPLUpdateService


class Symbol(BaseApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = GPLUpdateService()

    def quick_update(self):
        """快速更新股票基础信息 - 每天上午的01点31分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        res = self.client.quick_update_symbol(code_str, int(is_force))
        return self.success(res)

    def quick_update_ext(self):
        """快速更新股票额外信息 - 每天上午的16点06分"""
        code_str = self.params.get('code_str', '')
        res = self.client.quick_update_symbol_ext(code_str)
        return self.success(res)
