from tool.core import *
from utils.wechat.qywechat.command.base_command import BaseCommand
from service.ai.command.ai_command_service import AiCommandService


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
        response, aid = AiCommandService.question(self.content, self.user, 'QY_QUS')
        return self.send_content(response)

    def exec_0_4(self):
        """AI 百科"""
        response, aid = AiCommandService.science(self.content, self.user, 'QY_SCI')
        return self.send_content(response)

