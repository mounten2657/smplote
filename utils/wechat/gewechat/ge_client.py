import json
import requests
from typing import Optional
from tool.db.cache.redis_client import RedisClient
from utils.wechat.gewechat.factory.gewechat_client_factory import GewechatClientFactory
from tool.core import *

logger = Logger()


@Ins.singleton
class GeClient:

    ARGS_UNIQUE_KEY = True

    def __init__(self, config=None):
        self.config = config if config else Config.gewechat_config()
        self.appid = self.config.get('gewechat_app_id')
        self.client = self.get_gewechat_client()

    def get_token(self) -> Optional[str]:
        """
        获取gewechat token

        Returns:
            Optional[str]: 获取到的token，如果失败则返回None
        """
        config = self.config
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

    def get_gewechat_client(self):
        """
        获取GewechatClient实例
        使用ClientFactory确保全局只有一个实例
        Returns:
            GewechatClient 实例
        """
        config = self.config
        # 检查token是否存在，如果不存在则获取
        if not config.get('gewechat_token'):
            self.get_token()
        client = GewechatClientFactory.get_client(config)
        # 请关闭代理再执行登陆操作
        logger.info(f"尝试登录: {config.get('gewechat_app_id')}")
        GewechatClientFactory.login_if_needed(client, config.get('gewechat_app_id'))
        return client

    def set_gewechat_callback(self):
        """设置回调地址 - 消息订阅的关键"""
        config = self.config
        logger.debug("回调地址设置 - 请确保 Flask 处于运行中")
        callback_url = config['gewechat_callback_url']
        if not Config.is_prod():
            callback_url = Http.get_docker_inner_url(callback_url)
        try:
            client = self.client
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

    def get_friend_detail_info(self, wxid):
        """查询好友详细信息 - 有缓存"""
        # 先判断缓存中有无信息
        redis = RedisClient()
        cache_key = "GE_FRD_INFO"
        cache = redis.get(cache_key, [wxid])
        if cache:
            return cache
        res = self.client.get_detail_info(self.appid, [wxid])
        logger.debug(f"get_friend_detail_info - {res}")
        if res['ret'] == 200:
            data = res['data'][0]
            redis.set(cache_key, data, [wxid])
            return data
        return None

    def send_text_msg(self, text: str, to_wxid: str, ats: dict = None):
        """
        使用 gewechat 发送文本消息
        :param text:  消息内容
        :param to_wxid:  接收方的 wxid （人 或者 群聊）
        :param ats:  需要 @ 的成员 （仅群聊有效） - {"wxid": "xxx", "nickname": "yyy"}
        :return: 消息发送结果
        """
        if ats:
            text = f'@{ats.get('nickname')} {text}'
        return self.client.post_text(self.appid, to_wxid, text, ats.get('wxid', ''))

