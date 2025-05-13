from utils.wechat.gewechat.ge_client import GeClient
from utils.wechat.gewechat.callback.wechat_callback_handler import WechatCallbackHandler
from tool.core import *


class GeCallbackService:

    @staticmethod
    def reset_callback():
        return GeClient.set_gewechat_callback()

    @staticmethod
    def callback_handler():
        """微信回调入口"""
        # 自动转到 GET 或 POST 方法
        callback_handler = WechatCallbackHandler()
        method = Http.get_request_method()
        method = getattr(callback_handler, method)
        return method()


