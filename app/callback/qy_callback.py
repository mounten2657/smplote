from tool.router.base_app import BaseApp
from utils.wechat.qywechat.callback.qy_verify_handler import QyVerifyHandler
from utils.wechat.qywechat.callback.qy_callback_handler import QyCallbackHandler


class QyCallback(BaseApp):

    @classmethod
    def init_verify_wts(self):
        """企业微信自定义应用初始化验证 - WTS"""
        return QyVerifyHandler.verify('a1')

    @classmethod
    def collect_wts(self):
        """企业微信消息回调- WTS"""
        return QyCallbackHandler.msg_handler('a1')

    @classmethod
    def init_verify_gpl(self):
        """企业微信自定义应用初始化验证- GPL"""
        return QyVerifyHandler.verify('a2')

    @classmethod
    def collect_gpl(self):
        """企业微信消息回调- GPL"""
        return QyCallbackHandler.msg_handler('a2')
