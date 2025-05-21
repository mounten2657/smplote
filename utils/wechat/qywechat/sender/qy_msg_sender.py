from utils.wechat.qywechat.factory.qy_client_factory import QyClientFactory
from utils.grpc.open_nat.open_nat_client import OpenNatClient
from tool.core import Que, Ins


@Ins.singleton
class QyMsgSender(QyClientFactory, Que):

    _QY_API_MSG_SEND = '/cgi-bin/message/send'  # https://developer.work.weixin.qq.com/document/path/94677

    def __init__(self, app_key):
        Que.__init__(self)
        QyClientFactory.__init__(self, app_key)

    def send_message(self, content, msg_type, app_key):
        """给 QyClient 提供的调用方法"""
        return self.que_submit(content=content, msg_type=msg_type, app_key=app_key)

    def _que_exec(self, **kwargs):
        """队列执行入口"""
        content = kwargs.get('content')
        msg_type = kwargs.get('msg_type')
        app_key = kwargs.get('app_key')
        if not content:
            return False
        if msg_type == 'text':
            # 改为通过 vps 的 gRpc 发送
            return self._send_text_message_rpc(content, app_key)
        if msg_type == 'markdown':
            # 弃用 - 只能在企业微信中查看
            return self._send_md_message(content, app_key)
        return False

    def _send_text_message_rpc(self, content, app_key):
        """通过 vps  发送文本消息"""
        return OpenNatClient.send_text_msg(content, app_key)

    def _send_text_message(self, content, app_key):
        """
        发送文本消息 - 支持 a标签 和 换行符
        :param content: 消息内容
        :param app_key:  APP 账号 - a1 | a2 | ...
        :return: bool 执行结果
        """
        data = {
            "msgtype": 'text',
            "text": {
                "content": content
            }
        }
        return self._send_message(data, app_key)

    def _send_md_message(self, content, app_key):
        """
        发送 markdown 消息 - 目前只能在企业微信中查看
        :param content: 消息内容
        :param app_key:  APP 账号 - a1 | a2 | ...
        :return: bool 执行结果
        """
        data = {
            "msgtype": 'markdown',
            "markdown": {
                "content": content
            }
        }
        return self._send_message(data, app_key)

    def _send_message(self, data, app_key):
        """
        发送应用消息的底层方法
        :param data: 消息内容字典
        :param app_key:  APP 账号 - a1 | a2 | ...
        :return: bool 执行结果
        """
        self.refresh_config(app_key)
        url = f'{self._QY_API_MSG_SEND}?access_token={self.get_access_token()}'
        post_data = {
            "touser": self.user_list,
            "agentid": self.agent_id,
            "safe": 0
        }
        post_data.update(data)
        return self.qy_http_request(url, post_data)

