from tool.core import *
from utils.wechat.qywechat.sender.qy_msg_sender import QyMsgSender
from tool.unit.md.log_error_md import LogErrorMd

logger = Logger()


@Ins.singleton
class QyClient:

    ARGS_UNIQUE_KEY = True

    app_key = None

    def __init__(self, app_key='a1'):
        self.app_key = app_key
        self.msg_client = QyMsgSender(self.app_key)

    def set_app_key(self, app_key):
        """切换账号"""
        self.app_key = app_key
        return self

    def send_msg(self, content, msg_type='text'):
        """发送消息"""
        return self.msg_client.send_message(content, msg_type, self.app_key)

    def send_error_msg(self, result, log_id=None):
        """发送错误日志告警消息 - 仅生产环境"""
        if Config.is_prod():
            md = LogErrorMd.get_error_markdown(result, log_id)
            return self.send_msg(md)
        return False
