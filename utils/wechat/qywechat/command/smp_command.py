from tool.core import *
from utils.wechat.qywechat.command.base_command import BaseCommand


@Ins.singleton
class SmpCommand(BaseCommand):

    def exec_2_0(self):
        """SMP 设置"""
        return self.send_content()

    def exec_2_1(self):
        """SMP 刷新"""
        return self.send_content()

    def exec_2_2(self):
        """SMP 终端"""
        return self.send_content()

    def exec_2_3(self):
        """SMP 心跳"""
        return self.send_content()

