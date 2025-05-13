from tool.router.base_app_wx import BaseAppWx
from service.wechat.report.export_wechat_info import ExportWechatInfo


class Task(BaseAppWx):

    def daily_task(self):
        """每日自动化任务入口"""
        all_params = {
            "wxid": self.wxid,
            "g_wxid": self.g_wxid,
            "g_wxid_dir": self.g_wxid_dir,
            "params": self.params,
        }
        res = ExportWechatInfo.daily_task(all_params)
        return self.success(res)
