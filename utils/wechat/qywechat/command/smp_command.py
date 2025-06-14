from tool.core import Ins, Sys
from utils.wechat.qywechat.command.base_command import BaseCommand
from utils.wechat.vpwechat.vp_client import VpClient


@Ins.singleton
class SmpCommand(BaseCommand):

    def exec_2_0(self):
        """SMP KGU"""
        res = Sys.delay_kill_gu()
        content = f"正在执行 KGU 命令 - {res}\r\n\r\n请稍后查看结果……"
        return self.send_content(content)

    def exec_2_1(self):
        """SMP RGU"""
        res = Sys.delay_reload_gu()
        content = f"正在执行 RGU 命令 - {res}\r\n\r\n请稍后查看结果……"
        return self.send_content(content)

    def exec_2_2(self):
        """SMP RVP"""
        res = Sys.delay_reload_vp()
        content = f"正在执行 RVP 命令 - {res}\r\n\r\n请稍后查看结果……"
        return self.send_content(content)

    def exec_2_3(self):
        """SMP WLV"""
        res = VpClient().wakeup()
        content = f"{res}"
        return self.send_content(content)

    def exec_2_4(self):
        """SMP INF"""
        res = VpClient().get_login_status()
        content = f"{res}"
        return self.send_content(content)
