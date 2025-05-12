from tool.core import *
from utils.wechat.qywechat.command.base_command import BaseCommand
from utils.ai.client.ai_client_manager import AIClientManager


@Ins.singleton
class AiCommand(BaseCommand):

    def exec_0_0(self):
        """AI 设置"""
        return self.send_content()

    def exec_0_1(self):
        """AI 天气"""
        return self.send_content()

    def exec_0_2(self):
        """AI 点歌"""
        return self.send_content()

    def exec_0_3(self):
        """AI 提问"""
        content = str(self.content).replace('#提问', '').strip()
        if not content or content == 'None':
            txt = '请按 "#提问" 开头进行AI聊天，如：\r\n#提问 请推荐三首纯音乐'
            return self.send_content(txt)
        client = AIClientManager()
        prompt = '你是一个智能助手，请帮我回答一系列的问题，回答要简短有力，不要过度联想，语气要温和。'
        response = client.call_ai(content, prompt)
        response = f"{response}\r\n\r\n--此内容由AI生成，请仔细甄别--"
        return self.send_content(response)

    def exec_0_4(self):
        """AI 百科"""
        content = str(self.content).replace('#百科', '').strip()
        if not content or content == 'None':
            txt = '请按 "#百科" 开头进行AI科普，如：\r\n#百科 熊猫'
            return self.send_content(txt)
        client = AIClientManager()
        prompt = '你是一个科普助手，请根据我提供的关键词进行科普，回答要简短有力，不要过度联想，语气要温和。'
        response = client.call_ai(content, prompt)
        response = f"{response}\r\n\r\n--此内容由AI生成，请仔细甄别--"
        return self.send_content(response)

