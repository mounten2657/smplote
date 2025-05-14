import time
import threading
from service.source.preview.file_preview_service import FilePreviewService
from utils.wechat.gewechat.bridge.channel import Channel
from utils.wechat.gewechat.bridge.context import ContextType
from utils.wechat.gewechat.formatter.gewechat_message import GeWeChatMessage
from utils.wechat.gewechat.ge_client import GeClient
from tool.core import *

logger = Logger()
is_callback_success = False


class WechatCallbackHandler:

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # 使用_initialized=True创建配置，表示只初始化配置，不执行登录
            self.config = Config.gewechat_config()
            self.client = GeClient.get_gewechat_client(self.config)
            self.commands = self.config.get('gewechat_command_list').split(',')
            # 创建通道对象
            self.channel = Channel(self.client, self.config)
            self.message_queue = []  # 消息队列
            self.timer = None  # 定时器
            self.queue_lock = threading.Lock()  # 队列锁
            self.timer_lock = threading.Lock()  # 定时器锁
            self._initialized = True
            logger.debug("WechatCallbackHandler类初始化完成")

    def GET(self):
        # 搭建简单的文件服务器，用于向gewechat服务传输语音等文件，但只允许访问tmp目录下的文件
        logger.debug(f"处理微信回调消息[GET]===")
        if not Http.is_http_request():
            return 'success'
        params = Http.get_flask_params()
        logger.debug(f"处理微信回调消息[PAR]==={params}")

        file_path = params.get('file')
        if file_path:
            # 安全检查
            params['path'] = file_path
            return FilePreviewService.office(params)
        return "gewechat callback server is running"

    def POST(self):
        """处理微信回调消息"""
        logger.debug(f"处理微信回调消息[POST]===")
        if not Http.is_http_request():
            return 'success'

        global is_callback_success
        data = Http.get_flask_params()
        if not data:
            data = Http.get_flask_params()
        logger.debug(f"处理微信回调消息[DATA]==={data}".replace('\n', ' '))

        # gewechat服务发送的回调测试消息
        if isinstance(data, dict) and 'testMsg' in data and 'token' in data:
            logger.debug(f"收到回调测试消息: {data}")
            return "success"

        # 解析消息
        try:
            gewechat_msg = GeWeChatMessage(data, self.client)
        except Exception as e:
            logger.error(f"解析消息过程中出现错误: {str(e)}")
            return "success"

        # 过滤不需要处理的消息
        # 微信客户端的状态同步消息
        if gewechat_msg.ctype == ContextType.STATUS_SYNC:
            logger.debug("忽略状态同步消息")
            is_callback_success = True
            return "success"
        # 忽略非用户消息（如公众号、系统通知等）
        if gewechat_msg.ctype == ContextType.NON_USER_MSG:
            logger.debug(f"忽略非用户消息，来自 {gewechat_msg.from_user_id}: {gewechat_msg.content}")
            return "success"
        # 忽略来自自己的消息
        # if gewechat_msg.my_msg:
        #     logger.debug(f"忽略自己发送的消息: {gewechat_msg.content}")
        #     is_callback_success = True
        #     return "success"
        # 忽略过期的消息
        if int(gewechat_msg.create_time) < int(time.time()) - 60 * 5:  # 跳过5分钟前的历史消息
            logger.debug(f"忽略过期消息（5分钟前），来自 {gewechat_msg.actual_user_id}: {gewechat_msg.content}")
            return "success"
        if any(gewechat_msg.content.lower().startswith(prefix) for prefix in self.commands):
            logger.info(f"收到设置命令: {gewechat_msg.content}")
            self.channel.compose_context(gewechat_msg)
            return "success"
        else:
            # 处理有效消息
            try:
                with self.queue_lock:
                    self.message_queue.append(gewechat_msg)
                    logger.info(f"收到新消息，加入队列[1/{len(self.message_queue)}]: {gewechat_msg.content[:31]}")
                self.reset_timer()
            except Exception as e:
                logger.error(f"消息处理过程中出现错误: {str(e)}")
        return "success"

    def reset_timer(self):
        """重置定时器"""
        with self.timer_lock:
            # 如果存在定时器，先取消它
            if self.timer is not None:
                logger.debug("取消现有定时器")
                self.timer.cancel()
                self.timer = None

            # 获取等待时间
            wait_time = int(self.config.get("timer_seconds", '3'))
            # logger.debug(f"创建新的定时器，等待时间: {wait_time}秒")

            # 创建新的定时器
            self.timer = threading.Timer(wait_time, self.process_message_queue)
            self.timer.start()
            # logger.debug("新定时器已启动")

    def process_message_queue(self):
        """处理消息队列中的所有消息"""
        with self.queue_lock:
            if not self.message_queue:
                logger.debug("消息队列为空，跳过处理")
                return
            try:
                for msg in self.message_queue:
                    result = self.channel.compose_context(msg)
                    logger.info(f"消息处理完成，结果: {result}")
            except Exception as e:
                logger.error(f"消息处理过程中出现错误: {str(e)}")
            # 清空消息队列
            self.message_queue.clear()
            # 重置定时器为None
            with self.timer_lock:
                self.timer = None
                logger.debug("定时器已重置")

