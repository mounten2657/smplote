from utils.wechat.qywechat.qy_client import QyClient
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Config


class SendWxMsgService:

    @staticmethod
    def send_qy_msg(app_key, content):
        return QyClient(app_key).send_msg(content)

    @staticmethod
    def send_vp_msg(app_key, content):
        config = Config.vp_config()
        to_wxid = config['app_list'][app_key]['wxid']
        # 使用小号给主账号发消息
        return VpClient('a2').send_msg(content, to_wxid)

