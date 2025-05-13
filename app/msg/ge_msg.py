from tool.router.base_app_wx import BaseAppWx
from service.wechat.reply.send_wx_msg_service import SendWechatMsgService


class GeMsg(BaseAppWx):

    def send_msg(self):
        """通过链接请求发送微信私聊消息"""
        to_wxid = self.params.get('to_wxid', self.wxid)
        res = SendWechatMsgService.send_msg(self.params.get('text'), to_wxid)
        return self.success(res)

