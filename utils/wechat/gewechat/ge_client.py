import requests
import json
from typing import Optional
from utils.wechat.gewechat.factory.gewechat_client_factory import GewechatClientFactory
from tool.core import *

logger = Logger()


class GeClient:

    @staticmethod
    def set_gewechat_callback(config=None):
        """设置回调地址 - 消息订阅的关键"""
        logger.debug("回调地址设置 - 请确保 Flask 处于运行中")
        config = config if config else Config.gewechat_config()
        callback_url = Http.get_docker_inner_url(config['gewechat_callback_url'])
        try:
            client = GeClient.get_gewechat_client(config)
            callback_resp = client.set_callback(config['gewechat_token'], callback_url)
        except RuntimeError as e:
            callback_resp = Attr.parse_json_ignore(str(e))
        ret = False
        if callback_resp.get("ret") == 200:
            logger.info("回调地址设置成功")
            ret = True
        else:
            logger.warning(f"回调地址设置返回异常状态: {callback_resp}")
            logger.debug("继续运行，回调可能仍然有效...")
        return ret

    @staticmethod
    def get_token(config) -> Optional[str]:
        """
        获取gewechat token
        Returns:
            Optional[str]: 获取到的token，如果失败则返回None
        """
        url = config.get('gewechat_base_url', '') + "/tools/getTokenId"
        if not config.get('gewechat_base_url'):
            logger.error("缺少必要的配置参数：gewechat_base_url")
            return None
        try:
            response = requests.post(url, headers={}, data={})
            response.raise_for_status()  # 检查响应状态
            token = response.json()['data']
            logger.warning(f"Token未设置，已自动获取Token: {token}")
            Config.set_env('GEWECHAT_TOKEN', token)
            return token
        except requests.RequestException as e:
            logger.error(f"获取Token失败: {e}")
            return None
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"解析Token响应失败: {e}")
            return None

    @staticmethod
    def get_gewechat_client(config=None):
        """
        获取GewechatClient实例
        使用ClientFactory确保全局只有一个实例
        Returns:
            GewechatClient 实例
        """
        config = config if config else Config.gewechat_config()
        # 检查token是否存在，如果不存在则获取
        if not config.get('gewechat_token'):
            GeClient.get_token(config)
        # 使用工厂获取客户端实例
        client = GewechatClientFactory.get_client(config)
        # 如果不是初始化模式，并且没有app_id，则登录
        if 1 or not config.get('gewechat_app_id'):
            # 请关闭代理再执行登陆操作
            logger.info(f"尝试登录: {config.get('gewechat_app_id')}")
            GewechatClientFactory.login_if_needed(client, config.get('gewechat_app_id'))
        return client

    @staticmethod
    def send_text_msg(msg: str, wxid: str = None):
        """发送文本消息 - 可以是私聊，也可以是群聊，支持艾特"""
        return True

