from tool.router.base_app import BaseApp
from service.wechat.callback.ge_callback_service import GeCallbackService


class GeweCallback(BaseApp):

    def reset_callback(self):
        """重置回调地址"""
        res = GeCallbackService.reset_callback()
        return self.success(res)

    def collect(self):
        """微信回调入口"""
        return GeCallbackService.callback_handler()

