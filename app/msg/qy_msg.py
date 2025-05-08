from tool.router.base_app import BaseApp
from utils.wechat.qywechat.qy_client import QyClient


class QyMsg(BaseApp):

    _rule_list = {
        "send_msg": {
            "rule": {
                "content": "required|string|max:999",
                "msg_type": "string|max:20",
                "app_key": "string|in:a1,a2",
            }
        }
    }

    def send_msg(self):
        """通过链接请求发送企业应用消息"""
        content = self.params.get('content')
        msg_type = self.params.get('msg_type', 'text')
        app_key = self.params.get('app_key', 'a1')
        res = QyClient(app_key).send_msg(content, msg_type)
        return self.success(res)

