from utils.wechat.gewechat.wechat_client import WechatClient
from tool.core import *


class SendWechatMsg:

    @staticmethod
    def reset_callback():
        return WechatClient.set_gewechat_callback()

    @staticmethod
    def send_msg(msg: str, wxid: str = None):
        return True




