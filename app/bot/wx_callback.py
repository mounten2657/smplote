from tool.router.base_app import BaseApp
from utils.gewechat.wechat_callback_handler import WechatCallbackHandler
from service.wechat.reply.send_wechat_msg import SendWechatMsg
from tool.core import *


class WxCallback(BaseApp):

    def reset_callback(self):
        """重置回调地址"""
        res = SendWechatMsg.reset_callback()
        return self.success(res)

    def collect(self):
        """微信回调入口"""
        logger = Logger()
        callback_handler = WechatCallbackHandler()
        self.params['_msg'] = 'enter wx_callback ...'
        logger.info(self.params, 'WX_CALL')
        method = Http.get_request_method()
        method = getattr(callback_handler, method)
        return method()

