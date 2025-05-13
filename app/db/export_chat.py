from tool.router.base_app_wx import BaseAppWx
from service.wechat.report.export_wx_info_service import ExportWxInfoService


class ExportChat(BaseAppWx):

    def export_group_users(self):
        res = ExportWxInfoService.export_users(self.g_wxid, self.g_wxid_dir)
        return self.success(res)

    def export_group_chats(self):
        res = ExportWxInfoService.export_chats(self.g_wxid, self.g_wxid_dir, self.params)
        return self.success(res)

