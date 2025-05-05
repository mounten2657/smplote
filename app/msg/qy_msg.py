from tool.router.base_app import BaseApp
from utils.wechat.qywechat.qy_client import QyClient


class QyMsg(BaseApp):

    def send_msg(self):
        """通过链接请求发送企业应用消息"""
        app_key = self.params.get('app_key', 'a1')
        msg_type = self.params.get('msg_type', 'text')
        content = self.params.get('content')
        qy_client = QyClient(app_key)
        res = qy_client.send_msg(content, msg_type, app_key)
        return self.success(res)

