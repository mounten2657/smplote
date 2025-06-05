from service.wechat.report.export_wx_info_service import ExportWxInfoService
from service.wechat.callback.vp_command_service import VpCommandService
from tool.router.base_app_wx import BaseAppWx
from tool.core import Env, Sys


class Task(BaseAppWx):

    def index(self):
        """定时任务入口"""
        app_key = self.app_key
        s_wxid = Env.get('VP_WXID_A2')
        g_wxid = Env.get('VP_WXID_G2')
        tasks = {
            "vp_sky_rw_task": lambda: VpCommandService.vp_sky_rw_task(app_key, s_wxid, g_wxid)
        }
        res = {name: Sys.delayed_task(1, task) for name, task in tasks.items()}
        return self.success(res)

    def daily_task(self):
        """每日自动化任务入口 - 已弃用"""
        if self.wxid:
            return self.error('该接口已弃用！')
        all_params = {
            "wxid": self.wxid,
            "g_wxid": self.g_wxid,
            "g_wxid_dir": self.g_wxid_dir,
            "params": self.params,
        }
        res = ExportWxInfoService.daily_task(all_params)
        return self.success(res)
