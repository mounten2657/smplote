from tool.router.base_app_wx import BaseAppWx
from tool.core import *
from service.wechat.report.get_wx_info_service import GetWxInfoService


class RefreshChatDb(BaseAppWx):

    def refresh_wx_info(self):
        res = GetWxInfoService.get_real_time_wx_info(self.wxid)
        return self.success(res)

    def refresh_wx_core_db(self):
        res = GetWxInfoService.decrypt_wx_core_db(self.wxid, self.params)
        return self.success(res)

    def refresh_wx_real_time_db(self):
        res = GetWxInfoService.merge_wx_real_time_db(self.wxid)
        return self.success(res)

    def refresh_emoji(self):
        Emoji.download_all_emojis()
        return self.success()



