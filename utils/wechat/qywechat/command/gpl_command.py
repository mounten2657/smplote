from service.vpp.vpp_clash_service import VppClashService
from tool.core import Ins, Sys, Attr
from utils.wechat.qywechat.command.base_command import BaseCommand


@Ins.singleton
class GplCommand(BaseCommand):

    def exec_1_0(self):
        """GPL CMD-1"""
        res = VppClashService().get_traffic_stat()
        content = f"VSS执行结果:\r\n{res}\r\n"
        return self.send_content(content)

    def exec_1_1(self):
        """GPL CMD-2"""
        res = Sys.docker_stats()
        content = f"DSS执行结果:\r\n{res}\r\n"
        return self.send_content(content)

    def exec_1_2(self):
        """GPL CMD-3"""
        res = Sys.docker_ps()
        if Attr.get_by_point(res, '0.id'):
            res = "\r\n".join([f"{d['name']} - {d['status']} - {d['created']}" for d in res])
        content = f"DPS执行结果:\r\n{res}\r\n"
        return self.send_content(content)

    def exec_1_3(self):
        """GPL CMD-4"""
        return self.send_content()

    def exec_1_4(self):
        """GPL CMD-5"""
        return self.send_content()