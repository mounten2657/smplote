from utils.wechat.qywechat.qy_client import QyClient


class SendWxMsgService:

    @staticmethod
    def send_qy_msg(app_key, content):
        return QyClient(app_key).send_msg(content)

