from service.wechat.callback.vp_command_service import VpCommandService
from tool.core import Ins


@Ins.singleton
class VpMsgSender:

    def __init__(self, app_key = 'a1'):
        self.app_key = app_key

    def send_text_message(self, content, ats=None):
        """
        发送文本消息
        :param content: 消息内容
        :param ats: 需要 at 的人 - [{"wxid": "xxx", "nickname": "yyy"}]
        :return:  json - Data.isSendSuccess
        """
        commander = VpCommandService(self.app_key)
        return commander.vp_normal_msg(content, ats)

