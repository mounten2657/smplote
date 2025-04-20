from utils.gewechat.command.question_command import QuestionCommand
from utils.gewechat.command.setting_command import SettingCommand
from tool.core import Logger

logging = Logger()


class CommandManager:
    """
    命令管理器
    负责管理和执行各种命令
    """
    
    def __init__(self, channel):
        """
        初始化命令管理器
        
        Args:
            channel: 通信通道对象
        """
        self.channel = channel
        self.setting_command = SettingCommand(channel)
        self.question_command = QuestionCommand(channel)
        logging.info(f"已加载命令模块")
        
    def execute_setting_command(self, msg):
        """
        执行设置命令
        
        Returns:
            str: 命令执行结果
        """
        try:
            logging.info("执行命令")
            result = self.setting_command.execute(msg)
            logging.info(f"命令执行成功 - {result}")
            return result
        except Exception as e:
            error_msg = f"执行命令时出错: {str(e)}"
            logging.error(error_msg)
            return "error"

    def execute_question_command(self, msg):
        """智能提问"""
        try:
            logging.info("执行命令")
            result = self.question_command.execute(msg)
            logging.info(f"命令执行成功 - {result}")
            return result
        except Exception as e:
            error_msg = f"执行命令时出错: {str(e)}"
            logging.error(error_msg)
            return "error"



