from utils.ai.client.ai_client_manager import AIClientManager
from utils.gewechat.command.base_command import BaseCommand
from tool.core import Logger

logging = Logger()


class QuestionCommand(BaseCommand):
    """提问命令处理器"""
    
    @property
    def name(self):
        """命令名称"""
        return "提问"
        
    @property
    def description(self):
        """命令描述"""
        return "通过文字消息进行智能问答"
        
    @property
    def aliases(self):
        """命令别名"""
        return []
        
    @property
    def usage(self):
        """命令用法"""
        return "#提问 [具体问题]"
        
    def execute(self, msg=''):
        """
        执行提问操作

        Args:
            msg: 命令参数
        Returns:
            执行结果
        """
        try:
            text = msg.replace('#提问', '').strip()
            client = AIClientManager()
            prompt = '你是一个智能助手，请帮我回答一系列的问题，回答要简短有力，不要过度联想，语气要温和。'
            response = client.call_ai(text, prompt)

            # AI聊天
            response = f"[AI聊天] \n{response}"
            self.channel.send_sys_msg(response)

            logging.info(f"{response}")
            return "success"
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            self.channel.send_sys_msg(f"错误: {error_msg}")
            logging.error(error_msg)
            return "error"

