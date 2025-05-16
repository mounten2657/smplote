import time
from utils.wechat.gewechat.bridge.channel import Channel
from utils.wechat.gewechat.bridge.context import ContextType
from utils.wechat.gewechat.formatter.ge_msg_formatter import GeMsgFormatter
from tool.core import *

logger = Logger()


class WechatCallbackHandler:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = Config.gewechat_config()
        self.channel = Channel(self.config)
        logger.debug(f"{self.__class__.__name__}类初始化完成")

    def ge_handler(self, data):
        """处理微信回调消息"""
        logger.debug(f"处理微信回调消息[DATA]==={data}".replace('\n', ' '))
        if not data:
            return False

        # gewechat服务发送的回调测试消息
        if isinstance(data, dict) and 'testMsg' in data and 'token' in data:
            logger.debug(f"收到回调测试消息: {data}")
            return False

        try:
            # 解析消息
            gewechat_msg = GeMsgFormatter().parse_msg(data)
        except Exception as e:
            logger.error(f"解析消息过程中出现错误: {str(e)}")
            return False

        # 过滤不需要处理的消息
        if gewechat_msg.ctype == ContextType.STATUS_SYNC:
            logger.debug("忽略状态同步消息")
            return False
        if gewechat_msg.ctype == ContextType.NON_USER_MSG:
            logger.debug(f"忽略非用户消息，来自 {gewechat_msg.from_user_id}: {gewechat_msg.content}")
            return False
        if int(gewechat_msg.create_time) < int(time.time()) - 60 * 5:
            logger.debug(f"忽略过期消息（5分钟前），来自 {gewechat_msg.actual_user_id}: {gewechat_msg.content}")
            return False

        result = False
        try:
            logger.info(f"处理新消息: {gewechat_msg.content[:31]}")
            result = self.channel.compose_context(gewechat_msg)
            logger.info(f"消息处理完成，结果: {result}")
        except Exception as e:
            logger.error(f"消息处理过程中出现错误: {str(e)}")

        # 返回消息结构体以供上层应用处理
        return result


