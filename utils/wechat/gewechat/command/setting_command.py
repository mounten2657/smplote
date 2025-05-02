from utils.wechat.gewechat.command.base_command import BaseCommand
from tool.core import Logger

logging = Logger()


class SettingCommand(BaseCommand):
    """设置命令处理器"""
    
    @property
    def name(self):
        """命令名称"""
        return "设置"
        
    @property
    def description(self):
        """命令描述"""
        return "通过文字消息进行系统设置"
        
    @property
    def aliases(self):
        """命令别名"""
        return []
        
    @property
    def usage(self):
        """命令用法"""
        return "#设置 [具体参数]"
        
    def execute(self, msg=''):
        """
        执行设置命令

        Args:
            msg: 命令参数
        Returns:
            执行结果
        """
        try:
            master_name = self.config.get('master_name')

            # 发送欢迎语
            welcome_text = f"你好，欢迎使用 WTS！"
            self.channel.send_sys_msg(welcome_text)

            logging.info(f"已发送欢迎语 - {master_name} - {msg}")
            return "success"
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            self.channel.send_sys_msg(f"错误: {error_msg}")
            logging.error(error_msg)
            return "error"

