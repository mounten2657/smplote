from tool.router.base_app_wx import BaseAppWx
from service.wechat.report.get_wechat_info import GetWechatInfo


class GetChatInfo(BaseAppWx):

    def check_info(self):
        res = {"wx_config": self.wx_config}
        return self.success(res)

    def get_wx_info(self):
        res = GetWechatInfo.get_local_wx_info(self.wxid)
        return self.success(res)

    def get_users(self):
        res = GetWechatInfo.get_user_list(self.wxid, self.wxid_dir)
        return self.success(res)

    def get_chats(self):
        res = GetWechatInfo.get_chat_list(self.wxid, self.wxid_dir)
        return self.success(res)

    def get_sessions(self):
        res = GetWechatInfo.get_session_list(self.wxid, self.wxid_dir)
        return self.success(res)

    def get_rooms(self):
        res = GetWechatInfo.get_room_list(self.wxid, self.wxid_dir)
        return self.success(res)

