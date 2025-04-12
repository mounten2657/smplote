from tool.router.base_app import BaseApp
from tool.core import *
from tool.unit.wechat.get_wechat_info import GetWechatInfo


class RefreshChatDb(BaseApp):

    def refresh_wx_info(self):
        params = self.params()
        wxid = params.get('wxid') if params else ''
        res = GetWechatInfo.get_real_time_wx_info(wxid)
        return self.success(res)

    def refresh_wx_core_db(self):
        params = self.params()
        wxid = params.get('wxid') if params else ''
        start_time = params.get('start_time') if params else '0'
        res = GetWechatInfo.decrypt_wx_core_db(wxid, Str.int(start_time))
        return self.success(res)

    def refresh_wx_real_time_db(self):
        params = self.params()
        wxid = params.get('wxid') if params else ''
        res = GetWechatInfo.merge_wx_real_time_db(wxid)
        return self.success(res)

    def refresh_emoji(self):
        Emoji.download_all_emojis()
        return self.success()



