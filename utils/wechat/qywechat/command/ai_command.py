from tool.core import Ins, Http
from utils.wechat.vpwechat.vp_client import VpClient
from utils.wechat.qywechat.command.base_command import BaseCommand
from service.ai.command.ai_command_service import AiCommandService


@Ins.singleton
class AiCommand(BaseCommand):

    def exec_0_0(self):
        """AI 总览"""
        return self.send_content()

    def exec_0_1(self):
        """AI 风向"""
        return self.send_content()

    def exec_0_2(self):
        """AI 实时"""
        return self.send_content()

    def exec_0_3(self):
        """AI 日志"""
        return self.send_content()

    def exec_0_4(self):
        """AI 状态"""
        res = Http.send_request('GET', Http.get_base_url())
        content = f"{res}"
        return self.send_content(content)

    def qy_que(self):
        """AI 提问"""
        response, aid = AiCommandService.question(self.content, self.user, 'QY_QUS')
        return self.send_content(response)

    def qy_sci(self):
        """AI 百科"""
        response, aid = AiCommandService.science(self.content, self.user, 'QY_SCI')
        return self.send_content(response)

    def qy_wvp(self):
        """VP 唤醒登录"""
        res = VpClient().wakeup()
        response = f"正在执行 WVP 命令 - {res}\r\n\r\n请保持微信打开……"
        return self.send_content(response)
