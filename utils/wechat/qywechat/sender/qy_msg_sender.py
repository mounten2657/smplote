from tool.core import *
from utils.wechat.qywechat.factory.qy_client_factory import QyClientFactory

logger = Logger()


@Ins.singleton
class QyMsgSender(QyClientFactory, Que):

    ARGS_UNIQUE_KEY = True

    _QY_API_MSG_SEND = '/cgi-bin/message/send'

    def __init__(self, app_key='a1'):
        Que.__init__(self)
        QyClientFactory.__init__(self, app_key)

    def send_message(self, content, msg_type='text', app_key='a1'):
        logger.debug([app_key, msg_type, content], 'QY_MSG_SEND_SUB')
        """对外提供的开放方法"""
        return self.que_submit(content=content, msg_type=msg_type, app_key=app_key)

    def _que_exec(self, **kwargs):
        """队列执行方法入口"""
        content = kwargs.get('content')
        msg_type = kwargs.get('msg_type')
        app_key = kwargs.get('app_key')
        if not content:
            return False
        if msg_type == 'text':
            return self._send_text_message(content, app_key)
        return False

    def _send_text_message(self, msg, app_key):
        """
        发送文本消息
        :param msg: 文本内容
        :param app_key:  APP 账号 - a1 | a2 | ...
        :return: bool 执行结果
        """
        self.refresh_config(app_key)
        url = f'{self._QY_API_MSG_SEND}?access_token={self.get_access_token()}'
        data = {
            "touser": self.user_list,
            "agentid": self.agent_id,
            "msgtype": 'text',
            "text": {
                "content": msg
            },
            "safe": 0
        }
        return self.qy_http_request(url, data)
