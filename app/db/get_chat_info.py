from tool.router.base_app_wx import BaseAppWx
from service.wechat.report.get_wx_info_service import GetWxInfoService


class GetChatInfo(BaseAppWx):

    def check_info(self):
        res = {"wx_config": self.wx_config}
        return self.success(res)

    def get_wx_info(self):
        res = GetWxInfoService.get_local_wx_info(self.wxid)
        return self.success(res)

    def get_users(self):
        res = GetWxInfoService.get_user_list(self.wxid, self.wxid_dir)
        return self.success(res)

    def get_chats(self):
        res = GetWxInfoService.get_chat_list(self.wxid, self.wxid_dir)
        return self.success(res)

    def get_sessions(self):
        res = GetWxInfoService.get_session_list(self.wxid, self.wxid_dir)
        return self.success(res)

    def get_rooms(self):
        res = GetWxInfoService.get_room_list(self.wxid, self.wxid_dir)
        return self.success(res)

