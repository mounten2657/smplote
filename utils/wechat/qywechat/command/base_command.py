from utils.wechat.qywechat.qy_client import QyClient


class BaseCommand:

    _DEFAULT_MSG = '该功能正在开发中……'

    def __init__(self):
        self.client = QyClient()
        self.content = None
        self.user = None

    def set_content(self, content):
        self.content = content
        return True

    def set_user(self, user):
        self.user = user
        return True

    def exec_null(self):
        return True

    def send_content(self, content=None):
        content = content if content else self._DEFAULT_MSG
        return self.client.send_msg(content)

