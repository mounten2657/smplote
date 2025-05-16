from utils.wechat.gewechat.ge_client import GeClient
from utils.wechat.gewechat.command.command_manager import CommandManager
from tool.core import *

logger = Logger()


class Channel:
    def __init__(self, config):
        """
        初始化通信通道
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.app_id = config.get('gewechat_app_id')
        self.commands = self.config.get('gewechat_command_list').split(',')
        self.admins = self.config.get('gewechat_admin_list').split(',')
        self.rooms = self.config.get('gewechat_room_list').split(',')
        self.msg = None
        # 初始化命令管理器
        self.command_manager = CommandManager(self)

    def compose_context(self, message):
        """
        处理接收到的消息
        
        Args:
            message: 消息内容
            
        Returns:
            处理结果
        """
        self.msg = message
        logger.debug(f"队列处理消息 - {message}".replace('\n', ' '))
        # if not message.is_group:
        #     message.other_user_id = message.to_user_id
        #     message.other_user_nickname = message.to_user_nickname
        logger.info(f"消息ID - {message.msg_id}")
        logger.info(f"消息类型 - {message.ctype}")
        logger.info(f"消息时间 - {message.create_time}")
        logger.info(f"是否为自己的消息 - {message.my_msg}")
        logger.info(f"是否艾特自己 - {message.is_at}")
        logger.info(f"是否群聊 - {message.is_group}")
        logger.info(f"接收方wxid - {message.other_user_id}")
        logger.info(f"接收方昵称 - {message.other_user_nickname}")
        logger.info(f"发送方wxid - {message.actual_user_id}")
        logger.info(f"发送方昵称 - {message.actual_user_nickname}")
        logger.info(f"消息内容 - {message.content}".replace('\n', ' '))

        # 判断是否为设置命令
        if (any(message.content.lower().startswith(prefix) for prefix in self.commands)
                and message.other_user_id in self.rooms):
            logger.debug("检测到设置命令")
            if message.actual_user_id not in self.admins:
                return self.send_sys_msg('你还不是管理员，无法进行操作哦 t_t ')
            if message.content.lower().startswith('#设置'):
                result = self.command_manager.execute_setting_command(message.content)
            elif message.content.lower().startswith('#菜单'):
                result = '菜单功能正在开发中……'
                self.send_sys_msg(result)
            elif message.content.lower().startswith('#总结'):
                result = '总结功能正在开发中……'
                self.send_sys_msg(result)
            elif message.content.lower().startswith('#提问'):
                result = self.command_manager.execute_question_command(message.content)
            elif message.content.lower().startswith('#点歌'):
                result = '点歌功能正在开发中……'
                self.send_sys_msg(result)
            else:
                result = False
            logger.info(f"命令处理结果: {result}")
        else:
            logger.debug("处理文本消息")
            result = False
            # 是否 ai 提问
            if message.is_at and message.other_user_id in self.rooms:
                result = self.command_manager.execute_question_command(message.content)
            logger.info(f"消息处理结果: {result}")

        # 返回消息结构体以供上层应用处理
        return self.msg

    def send_sys_msg(self, text):
        """发送系统消息"""
        # 从哪里来的消息就发送到哪里去
        message = self.msg
        ats = None
        if not message.my_msg or not message.is_group:
            ats = {"wxid": message.actual_user_id, "nickname": message.actual_user_nickname}
        GeClient().send_text_msg(text, message.other_user_id, ats)
        return text



