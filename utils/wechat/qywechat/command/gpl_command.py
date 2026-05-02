from service.vpp.vpp_clash_service import VppClashService
from tool.core import Ins, Sys
from utils.wechat.qywechat.command.base_command import BaseCommand


@Ins.singleton
class GplCommand(BaseCommand):

    def exec_1_0(self):
        """GPL CMD-1"""
        res = VppClashService().get_traffic_stat()
        content = f"正在执行 VSS 命令 - {res}\r\n\r\n请稍后查看结果……"
        return self.send_content(content)

    def exec_1_1(self):
        """GPL CMD-2"""
        res = Sys.docker_stats()
        content = f"正在执行 DSS 命令 - {res}\r\n\r\n请稍后查看结果……"
        return self.send_content(content)

    def exec_1_2(self):
        """GPL CMD-3"""
        res = Sys.docker_ps()
        content = f"正在执行 DPS 命令 - {res}\r\n\r\n请稍后查看结果……"
        return self.send_content(content)

    def exec_1_3(self):
        """GPL CMD-4"""
        return self.send_content()

    def exec_1_4(self):
        """GPL CMD-5"""
        return self.send_content()