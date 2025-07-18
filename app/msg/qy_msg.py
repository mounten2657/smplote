from tool.router.base_app import BaseApp
from service.wechat.reply.send_wx_msg_service import SendWxMsgService


class QyMsg(BaseApp):

    _rule_list = {
        "send_msg": {
            "method": ["GET", "POST"],
            "rule": {
                "content": "required|string|max:999",
                "app_key": "string|in:a1,a2",
            }
        }
    }

    def send_msg(self):
        """通过链接发送企业应用消息"""
        content = self.params.get('content')
        res = SendWxMsgService.send_qy_msg(self.app_key, content)
        return self.success(res)

