from tool.router.base_app import BaseApp
from tool.unit.wechat.export_wechat_info import ExportWechatInfo


class ExportChat(BaseApp):

    def export_group_users(self):
        res = ExportWechatInfo.export_users(self.g_wxid, self.db_config, self.g_wxid_dir)
        return self.success(res)

    def export_group_chats(self):
        res = ExportWechatInfo.export_chats(self.g_wxid, self.db_config, self.g_wxid_dir, self.params)
        return self.success(res)

