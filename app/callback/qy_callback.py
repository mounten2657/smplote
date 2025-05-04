from tool.router.base_app import BaseApp
from utils.wechat.qywechat.callback.qy_verify_handler import QyVerifyHandler
from utils.wechat.qywechat.callback.qy_callback_handler import QyCallbackHandler


class QyCallback(BaseApp):

    def collect_wts(self):
        """企业微信消息回调- WTS"""
        if self.http_method == 'GET':
            # 初始化验证 - 一般只走一次
            return QyVerifyHandler.verify('a1')
        return QyCallbackHandler.msg_handler('a1')

    def collect_gpl(self):
        """企业微信消息回调- GPL"""
        if self.http_method == 'GET':
            # 初始化验证 - 一般只走一次
            return QyVerifyHandler.verify('a2')
        return QyCallbackHandler.msg_handler('a2')
