from service.vpp.vpp_clash_service import VppClashService
from service.source.nat_service import NatService
from tool.core import Ins, Sys, Attr
from utils.wechat.qywechat.command.base_command import BaseCommand


@Ins.singleton
class GplCommand(BaseCommand):

    def exec_1_0(self):
        """GPL VSS"""
        res = VppClashService().get_traffic_stat()
        content = f"VSS执行结果:\r\n{res}\r\n"
        return self.send_content(content)

    def exec_1_1(self):
        """GPL DSS"""
        res = Sys.docker_stats()
        if Attr.get_by_point(res, '0.id'):
            res = "\r\n".join([f"{d['name']} | {d['cpu_percent']} | {d['mem_usage']} / {d['mem_limit']} | {d['mem_percent']}" for d in res])
        content = f"DSS执行结果:\r\n{res}"
        return self.send_content(content)

    def exec_1_2(self):
        """GPL DPS"""
        res = Sys.docker_ps()
        if Attr.get_by_point(res, '0.id'):
            res = "\r\n".join([f"{d['name']} | {d['status']} | {d['created']}" for d in res])
        content = f"DPS执行结果:\r\n{res}"
        return self.send_content(content)

    def exec_1_3(self):
        """GPL CLR"""
        res = NatService().clean_mixed_request()
        content = f"CLR执行结果:\r\n{res}\r\n"
        return self.send_content(content)

    def exec_1_4(self):
        """GPL STA"""
        return self.send_content()