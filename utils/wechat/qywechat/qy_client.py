from tool.core import *
from utils.wechat.qywechat.sender.qy_msg_sender import QyMsgSender
from utils.grpc.open_nat.open_nat_client import OpenNatClient

logger = Logger()


@Ins.singleton
class QyClient:

    ARGS_UNIQUE_KEY = True

    APP_KEY = None

    def __init__(self, app_key='a1'):
        self.APP_KEY = app_key
        self.msg_client = QyMsgSender(self.APP_KEY)

    def send_msg(self, content, msg_type='text'):
        """发送消息"""
        # return self.msg_client.send_message(content, msg_type, self.APP_KEY)
        # 改为通过 vps 的 gRpc 发送
        return OpenNatClient.send_text_msg(content, self.APP_KEY)
