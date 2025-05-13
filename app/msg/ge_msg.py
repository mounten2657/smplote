from tool.router.base_app_wx import BaseAppWx
from service.wechat.reply.send_wechat_msg import SendWechatMsg


class GeMsg(BaseAppWx):

    def send_msg(self):
        """通过链接请求发送微信私聊消息"""
        res = SendWechatMsg.send_msg(self.params.get('text'), self.wxid)
        return self.success(res)

