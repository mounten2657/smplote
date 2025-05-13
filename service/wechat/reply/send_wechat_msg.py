from utils.wechat.gewechat.ge_client import GeClient
from tool.core import *


class SendWechatMsg:

    @staticmethod
    def reset_callback():
        return GeClient.set_gewechat_callback()

    @staticmethod
    def send_msg(msg: str, wxid: str = None):
        return True




