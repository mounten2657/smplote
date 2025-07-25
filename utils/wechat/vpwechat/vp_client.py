import threading
from utils.wechat.vpwechat.factory.vp_base_factory import VpBaseFactory
from utils.wechat.vpwechat.factory.vp_socket_factory import VpSocketFactory
from utils.wechat.vpwechat.factory.vp_client_factory import VpClientFactory
from tool.db.cache.redis_client import RedisClient
from tool.core import Logger, Sys, Ins, Attr, Str, Time

logger = Logger()


@Ins.singleton
class VpClient(VpBaseFactory):

    ARGS_UNIQUE_KEY = True

    def __init__(self, app_key='a1'):
        super().__init__(app_key)
        self.client = VpClientFactory(self.config, self.app_key)

    def start_websocket(self):
        """延迟启动 websocket"""
        def ws_start():
            Time.sleep(Str.randint(1, 10))
            # 确保只能有一个 socket
            redis = RedisClient()
            cache_key = 'LOCK_WSS_CNT'
            if redis.get(cache_key):
                return False
            redis.set(cache_key, 1)
            logger.debug('websocket starting', 'WS_STA')
            ws = VpSocketFactory(self.app_key)
            return ws.start()
        # res = Sys.delayed_task(3, ws_start)
        thread = threading.Thread(target=ws_start, daemon=True)
        thread.start()
        logger.debug(f'websocket start done', 'WS_END')
        return True

    def close_websocket(self, is_all=0):
        """关闭 websocket"""
        def ws_close():
            logger.debug(f'websocket close - {is_all}', 'WS_CED')
            RedisClient().delete('LOCK_WSS_CNT')
            if is_all:
                VpSocketFactory('a1').close()
                VpSocketFactory('a2').close()
                return True
            ws = VpSocketFactory(self.app_key)
            return ws.close()
        res = Sys.delayed_task(1, ws_close)
        logger.debug(f'websocket close done {is_all} - {res}', 'WS_END')
        return res

    def send_msg(self, content, to_wxid, ats=None, extra=None):
        """发送文本消息"""
        return self.client.send_text_message(content, to_wxid, ats, extra)

    def send_img_msg(self, image_path, to_wxid, extra=None):
        """发送图片消息"""
        return self.client.send_img_message(image_path, to_wxid, extra)

    def send_voice_message(self, mp3_path, to_wxid, extra=None):
        """发送语音消息"""
        return self.client.send_voice_message(mp3_path, to_wxid, extra)

    def send_dg_message(self, res, to_wxid, extra=None):
        """发送点歌消息"""
        return self.client.send_dg_message(res, to_wxid, extra)

    def send_card_message(self, res, to_wxid, extra=None):
        """发送卡片消息"""
        return self.client.send_card_message(res, to_wxid, extra)

    def get_login_status(self):
        """获取登陆状态"""
        return self.client.get_login_status()

    def refresh_user(self, wxid, g_wxid=''):
        """刷用户缓存"""
        key_list = ['VP_USER_INFO', 'VP_USER_FRD_INF', 'VP_USER_FRD_RAL', 'VP_USER_FRD_LAB']
        list(map(lambda key: RedisClient().delete(key, [wxid]), key_list))
        return self.get_user(wxid, g_wxid)

    @Ins.cached('VP_USER_INFO')
    def get_user(self, wxid, g_wxid=''):
        """获取完整的用户信息"""
        user_info = self.get_user_frd_inf(wxid, g_wxid)
        label = self.get_user_frd_lab()
        user_info = Attr.get_by_point(user_info, 'Data.contactList.0', {})
        label = Attr.get_by_point(label, 'Data.labelPairList', [])
        user = {
            "wxid": Attr.get_by_point(user_info, 'userName.str', ''),
            "nickname": Attr.get_by_point(user_info, 'nickName.str', ''),
            "remark_name": Attr.get_by_point(user_info, 'remark.str', ''),
            "quan_pin": Attr.get_by_point(user_info, 'quanPin.str', ''),
            "sex": Attr.get_by_point(user_info, 'sex', ''),
            "p_wxid": Attr.get_by_point(user_info, 'alias', ''),
            "encry_name": Attr.get_by_point(user_info, 'encryptUserName', ''),
            "country": Attr.get_by_point(user_info, 'country', ''),
            "province": Attr.get_by_point(user_info, 'province', ''),
            "signature": Attr.get_by_point(user_info, 'signature', ''),
            "sns_img_url": Attr.get_by_point(user_info, 'snsUserInfo.sns_bgimg_id', ''),
            "sns_privacy": Attr.get_by_point(user_info, 'snsUserInfo.sns_privacy_recent', ''),
            "head_img_url": Attr.get_by_point(user_info, 'bigHeadImgUrl', ''),
            "head_img_url_small": Attr.get_by_point(user_info, 'smallHeadImgUrl', ''),
            "description": Attr.get_by_point(user_info, 'description', ''),
            "label_id_list": Attr.get_by_point(user_info, 'labelIdlist', ''),
            "label_name_list": Attr.get_by_point(user_info, 'labelIdlist', ''),
            "phone_list": Attr.get_by_point(user_info, 'phoneNumListInfo.phoneNumList', []),
            "is_friend": 0 if g_wxid else self.get_user_is_friend(wxid),
            "cached": 1,
        }
        # 转换处理
        user.update({
            "label_name_list": ",".join(lb["labelName"] for lb in label if str(lb["labelId"]) in user["label_id_list"].split(",")),
            "phone_list": ",".join(str(phone["phoneNum"]) for phone in user["phone_list"])
        })
        return user

    def get_user_is_friend(self, wxid):
        relation = self.get_user_frd_ral(wxid)
        return int(Attr.get_by_point(relation, 'Data.FriendRelation', -1) == 0)

    @Ins.cached('VP_USER_FRD_INF')
    def get_user_frd_inf(self, wxid, g_wxid):
        return self.client.get_friend_info([wxid], g_wxid)

    @Ins.cached('VP_USER_FRD_RAL')
    def get_user_frd_ral(self, wxid):
        return self.client.get_friend_relation(wxid)

    @Ins.cached('VP_USER_FRD_LAB')
    def get_user_frd_lab(self):
        return self.client.get_label_list()

    def refresh_room(self, g_wxid):
        """刷群聊缓存"""
        key_list = ['VP_ROOM_INFO', 'VP_ROOM_GRP_INF', 'VP_ROOM_GRP_USL', 'VP_ROOM_GRP_NTC']
        list(map(lambda key: RedisClient().delete(key, [g_wxid]), key_list))
        return True

    @Ins.cached('VP_ROOM_INFO')
    def get_room(self, g_wxid):
        """获取完整的群聊信息"""
        room_info = self.get_room_grp_info(g_wxid)
        notice = self.get_room_grp_ntc(g_wxid)
        members = self.get_room_grp_usl(g_wxid)
        room_info = Attr.get_by_point(room_info, 'Data.contactList.0', {})
        members = Attr.get_by_point(members, 'Data.member_data.chatroom_member_list', [])
        room = {
            "g_wxid": Attr.get_by_point(room_info, 'userName.str', ''),
            "nickname": Attr.get_by_point(room_info, 'nickName.str', ''),
            "quan_pin": Attr.get_by_point(room_info, 'quanPin.str', ''),
            "owner": Attr.get_by_point(room_info, 'chatRoomOwner', ''),
            "head_img_url": Attr.get_by_point(room_info, 'smallHeadImgUrl', ''),
            "encry_name": Attr.get_by_point(room_info, 'encryptUserName', ''),
            "member_count": Attr.get_by_point(room_info, 'newChatroomData.member_count', 0),
            "notice": Attr.get_by_point(notice, 'Data.chatRoomName', ''),
            "remark": "",
            "member_list": [],
            "cached": 1,
        }
        # 只需要 wxid 和 显示名 - 其它信息由 get_user 补全
        room.update({"member_list": [
            {
                "wxid": m.get('user_name', 'null'),
                "display_name": m.get("display_name", m.get("nick_name", 'null'))
            }
            for m in members
        ]})
        return room

    @Ins.cached('VP_ROOM_GRP_INF')
    def get_room_grp_info(self, g_wxid):
        return self.client.get_room_info(g_wxid)

    @Ins.cached('VP_ROOM_GRP_NTC')
    def get_room_grp_ntc(self, g_wxid):
        return self.client.get_room_notice(g_wxid)

    @Ins.cached('VP_ROOM_GRP_USL')
    def get_room_grp_usl(self, g_wxid):
        return self.client.get_room_user_list(g_wxid)

    def download_file(self, message):
        """下载文件"""
        return self.client.download_file(message)

    def get_login_user(self):
        """获取登陆用户信息"""
        return self.client.get_friend_info([self.self_wxid])

    def wakeup(self):
        """唤醒登录"""
        user_info = self.get_login_user()
        user_info = Attr.get_by_point(user_info, 'Data.contactList.0', {})
        user_name = Attr.get_by_point(user_info, 'userName.str', '')
        if user_name:
            return {"Code": 202, "Data": {}, "Text": "设备在线无需重复登录"}
        return self.client.wakeup_login()
