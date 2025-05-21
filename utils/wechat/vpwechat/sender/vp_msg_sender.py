from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Que, Ins


@Ins.singleton
class VpMsgSender(Que):

    def __init__(self, app_key = 'a1'):
        Que.__init__(self)
        self.client = VpClient(app_key)

    def send_text_message(self, content, to_wxid, ats=None):
        """给 VpClient 提供的调用方法"""
        return self.que_submit(content=content, to_wxid=to_wxid, ats=ats)

    def _que_exec(self, **kwargs):
        """队列执行入口"""
        content = kwargs.get('content')
        to_wxid = kwargs.get('to_wxid')
        ats = kwargs.get('ats')
        if not content:
            return False
        return self._send_text_message(content, to_wxid, ats)

    def _send_text_message(self, content, to_wxid, ats):
        """
        发送文本消息
        :param content: 消息内容
        :param to_wxid: 接收者wxid
        :param ats: 需要 at 的人 - [{"wxid": "xxx", "nickname": "yyy"}]
        :return:  json - Data.isSendSuccess
        """
        return self.client.send_msg(content, to_wxid, ats)

