from utils.grpc.open_nat.open_nat_client import OpenNatClient


class OpenNatService:

    @staticmethod
    def init_vps_config_qy():
        return OpenNatClient.init_config_qy()

    @staticmethod
    def send_text_msg(content, app_key='a1', user_list=None, vc='z2'):
        """发送企业文本消息 - 默认使用  z2 - IP 不常变"""
        return OpenNatClient(vc).send_wechat_text(content, app_key, user_list)

    @staticmethod
    def send_http_request(method, url, params=None, headers=None, timeout=None, vc=None):
        """发起http请求并返回结果"""
        return OpenNatClient(vc).open_nat_http(method, url, params, headers, timeout)
