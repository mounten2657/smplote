from utils.grpc.open_nat.open_nat_client import OpenNatClient


class OpenNatService:

    @staticmethod
    def init_vps_config_qy():
        return OpenNatClient.init_config_qy()

    @staticmethod
    def send_text_msg(content, app_key='a1', user_list=None):
        """发送文本消息 - 对外方法"""
        return OpenNatClient().send_wechat_text(content, app_key, user_list)

    @staticmethod
    def send_http_request(method, url, params=None, headers=None, timeout=None):
        """发起http请求并返回结果"""
        return OpenNatClient().open_nat_http(method, url, params, headers, timeout)
