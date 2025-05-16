from utils.wechat.gewechat.ge_client import GeClient


class SendWechatMsgService:

    @staticmethod
    def send_msg(msg: str, wxid: str = None):
        return GeClient().send_text_msg(msg, wxid)
