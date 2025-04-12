from tool.router.base_app import BaseApp
from tool.unit.wechat.get_wechat_info import GetWechatInfo


class GetChatInfo(BaseApp):

    def check_info(self):
        res = {"wx_config": self.wx_config, "db_config": self.db_config}
        return self.success(res)

    def get_wx_info(self):
        res = GetWechatInfo.get_local_wx_info(self.wxid)
        return self.success(res)

    def get_users(self):
        res = GetWechatInfo.get_user_list(self.wxid, self.db_config, self.wxid_dir)
        return self.success(res)

    def get_chats(self):
        res = GetWechatInfo.get_chat_list(self.wxid, self.db_config, self.wxid_dir)
        return self.success(res)

    def get_sessions(self):
        res = GetWechatInfo.get_session_list(self.wxid, self.db_config, self.wxid_dir)
        return self.success(res)

    def get_rooms(self):
        res = GetWechatInfo.get_room_list(self.wxid, self.db_config, self.wxid_dir)
        return self.success(res)

