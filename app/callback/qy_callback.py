from tool.router.base_app import BaseApp
from utils.wechat.qywechat.callback.qy_callback_handler import QyCallbackHandler


class QyCallback(BaseApp):

    def collect_wts(self):
        """企业微信消息回调- WTS"""
        return QyCallbackHandler().msg_handler('a1', self.params)

    def collect_gpl(self):
        """企业微信消息回调- GPL"""
        return QyCallbackHandler().msg_handler('a2', self.params)
