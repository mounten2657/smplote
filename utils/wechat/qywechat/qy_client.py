from tool.core import *
from utils.wechat.qywechat.sender.qy_msg_sender import QyMsgSender

logger = Logger()


@Ins.singleton
class QyClient:

    def __init__(self, app_key='a1'):
        self.msg_client = QyMsgSender(app_key)

    def send_msg(self, content, msg_type, app_key):
        """发送消息"""
        return self.msg_client.send_message(content, msg_type, app_key)
