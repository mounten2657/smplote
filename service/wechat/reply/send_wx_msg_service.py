from service.wechat.callback.vp_command_service import VpCommandService
from utils.wechat.qywechat.qy_client import QyClient


class SendWxMsgService:

    @staticmethod
    def send_qy_msg(app_key, content):
        return QyClient(app_key).send_msg(content)

    @staticmethod
    def send_vp_msg(app_key, content):
        commander = VpCommandService(app_key)
        return commander.vp_normal_msg(content)

