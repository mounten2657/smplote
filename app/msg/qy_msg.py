from tool.router.base_app import BaseApp
from utils.wechat.qywechat.qy_client import QyClient


class QyMsg(BaseApp):

    def send_msg(self):
        """通过链接请求发送企业应用消息"""
        params = self.params
        app_key = params.get('app_key', 'a1')
        qy_client = QyClient(app_key)
        res = qy_client.send_msg(params.get('text'), 'text', app_key)
        return self.success(res)

