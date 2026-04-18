from tool.router.base_app import BaseApp
from service.wechat.callback.qy_callback_service import QyCallbackService


class QyCallback(BaseApp):

    def collect_wts(self):
        """企业微信消息回调- WTS"""
        return QyCallbackService().qy_callback_handler('a1', self.params)

    def collect_gpl(self):
        """企业微信消息回调- GPL"""
        return QyCallbackService().qy_callback_handler('a2', self.params)
