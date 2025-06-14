from tool.core import Ins
from utils.wechat.qywechat.command.base_command import BaseCommand


@Ins.singleton
class GplCommand(BaseCommand):

    def exec_1_0(self):
        """GPL CMD-1"""
        return self.send_content()

    def exec_1_1(self):
        """GPL CMD-2"""
        return self.send_content()

    def exec_1_2(self):
        """GPL CMD-3"""
        return self.send_content()
