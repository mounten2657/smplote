from tool.router.base_app import BaseApp
from tool.core import *
from service.wechat.report.get_wechat_info import GetWechatInfo


class RefreshChatDb(BaseApp):

    def refresh_wx_info(self):
        res = GetWechatInfo.get_real_time_wx_info(self.wxid)
        return self.success(res)

    def refresh_wx_core_db(self):
        res = GetWechatInfo.decrypt_wx_core_db(self.wxid, self.params)
        return self.success(res)

    def refresh_wx_real_time_db(self):
        res = GetWechatInfo.merge_wx_real_time_db(self.wxid)
        return self.success(res)

    def refresh_emoji(self):
        Emoji.download_all_emojis()
        return self.success()



