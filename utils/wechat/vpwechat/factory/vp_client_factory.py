from tool.core import Logger, Http, Time
from model.wechat.wechat_api_log_model import WechatApiLog

logger = Logger()


class VpClientFactory:

    def __init__(self, config):
        self.base_url = f"http://{config['ws_host']}:{config['ws_port']}"
        self.key = config['token_key']

    def _api_call(self, method: str, uri: str, body: dict = None, biz_code: str = 'NULL'):
        """
        发起 wechatpad http 请求
        :param method:  http 请求方式
        :param uri:  请求路径
        :param body:  post 数据
        :param biz_code:  业务码
        :return: json
        """
        start_time = Time.now(0)
        url = f"{self.base_url}{uri}?key={self.key}"
        logger.debug(f'VP API 请求参数:  {biz_code} - {method}[{uri}] - {body}', 'VP_API_CALL_STA')
        # 请求数据入库
        db = WechatApiLog()
        pid = db.add_log(method, uri, body, biz_code)
        # 执行接口请求
        method = 'JSON' if 'POST' == method else method
        res = Http.send_request(method, url, body)
        logger.debug(f'VP API 请求结果: {res}', 'VP_API_CALL_RET')
        # 更新执行结果
        run_time = round(Time.now(0) - start_time, 3) * 1000  # 执行时间单位为毫秒
        update_data = {"response_time": run_time, "response_result": res}
        if res.get('Code') == 200:
            update_data.update({"is_succeed": 1})
        db.update_log(pid, update_data)
        return res

    def get_login_status(self):
        """
        获取在线状态
        :return: json - Data.loginState=1 代表在线
        {"Code":200,"Data":{"loginState":1,"expiryTime":"2026-05-17","loginErrMsg":"账号在线状态良好！","loginJournal":{"count":0,"logs":[]},"loginTime":"2025-05-17 05:38:56","onlineDays":0,"onlineTime":"本次在线: 0天0时7分","proxyUrl":"","targetIp":"223.152.206.237:8849","totalOnline":"总计在线: 0天0时8分"},"Text":""}
        """
        api = '/login/GetLoginStatus'
        return self._api_call('GET', api, None, 'VP_LGS')

    def send_text_message(self, content, to_wxid, ats=None):
        """
        发送文本消息
        :param content: 消息内容
        :param to_wxid: 接收者wxid
        :param ats: 需要 at 的人 - [{"wxid": "xxx", "nickname": "yyy"}]
        :return:  json - Data.isSendSuccess
        {"Code":200,"Data":[{"isSendSuccess":true,"resp":{},"textContent":"Hello World","toUSerName":"xxx"}],"Text":""}
        """
        if not content or not to_wxid:
            return False
        api = '/message/SendTextMessage'
        at_wxid_list = []
        if ats:
            at_str = ''
            for at in ats:
                at_wxid_list.append(at['wxid'])
                at_str += f"@{at['nickname']}"
            content = f"{at_str} {content}"
        body = {
            "MsgItem": [{
                "AtWxIDList": at_wxid_list,
                "ImageContent": "",
                "MsgType": 1,
                "TextContent": content,
                "ToUserName": to_wxid,

            }]
        }
        return self._api_call('POST', api, body, 'VP_SMG')

    def get_room_info(self, g_wxid):
        """
        获取群详情
        :param g_wxid: 群聊wxid
        :return: json - Data.contactList.0.chatRoomOwner
        {"Code":200,"Data":{"contactCount":1,"contactList":[{"userName":{"str":"xxx@chatroom"},"nickName":{"str":"robot"},"quanPin":{"str":"robot"},"chatRoomOwner":"wxid_xxx","smallHeadImgUrl":"https://wx.qlogo.cn/mmcrhead/xxx/0","encryptUserName":"v3_xxx@stranger","chatroomVersion":10007,"chatroomMaxCount":500,"chatroomAccessType":0,"newChatroomData":{"member_count":2,"chatroom_member_list":[{"user_name":"wxid_xxx","nick_name":"xxx","chatroom_member_flag":1,"unknow":"wxid_xxx"}]},"deleteFlag":0,"chatroomStatus":524288,"extFlag":0}],"ret":"AA=="},"Text":""}
        """
        if not g_wxid:
            return False
        api = '/group/GetChatRoomInfo'
        body = {"ChatRoomWxIdList": [g_wxid]}
        return self._api_call('POST', api, body, 'VP_GRP')

    def get_room_notice(self, g_wxid):
        """
        获取群公告
        :param g_wxid: 群聊wxid
        :return: json - Data.chatRoomName
        {"Code":200,"Data":{"baseRequest":{},"chatRoomName":"Notice - 群公告 🔔🎁📫🔒"},"Text":""}
        """
        if not g_wxid:
            return False
        api = '/group/SetGetChatRoomInfoDetail'
        body = {"ChatRoomName": g_wxid}
        return self._api_call('POST', api, body, 'VP_GRP')

    def get_room_user_list(self, g_wxid):
        """
        获取群成员详细
        :param g_wxid: 群聊wxid
        :return: json - Data.member_data.chatroom_member_list.0
        {"Code":200,"Data":{"base_response":{"ret":0,"errMsg":{}},"chatroom_wxid":"xxx@chatroom","client_version":10007,"member_data":{"member_count":20,"chatroom_member_list":[{"user_name":"wxid_xxx","nick_name":"xxx","display_name":"🥇xxx","big_head_img_url":"https://wx.qlogo.cn/mmhead/ver_1/xxx/0","small_head_img_url":"https://wx.qlogo.cn/mmhead/ver_1/xxx/132","chatroom_member_flag":1}],"info_mask":0,"unknow":{}}},"Text":""}
        """
        if not g_wxid:
            return False
        api = '/group/GetChatroomMemberDetail'
        body = {"ChatRoomName": g_wxid}
        return self._api_call('POST', api, body, 'VP_GRP')

    def get_friend_info(self, wxid, g_wxid = ''):
        """
        获取联系人详情
        :param wxid: 联系人wxid
        :param g_wxid: 群聊wxid
        :return: json - Data.contactList.0.description
        {"Code":200,"Data":{"contactCount":1,"contactList":[{"userName":{"str":"wxid_xxx"},"nickName":{"str":"x"},"quanPin":{"str":"ci"},"sex":1,"remark":{"str":"🏅x"},"contactType":0,"province":"Offaly","signature":"花开花落花相似，人来人往人不同","hasWeiXinHdHeadImg":1,"alias":"weixinhao","snsUserInfo":{"sns_flag":1,"sns_bgimg_id":"http://szmmsns.qpic.cn/mmsns/xxx/0","sns_bgobject_id":14563952301353996000,"sns_flagex":7297,"sns_privacy_recent":72},"country":"IE","bigHeadImgUrl":"https://wx.qlogo.cn/mmhead/ver_1/xxx/0","smallHeadImgUrl":"https://wx.qlogo.cn/mmhead/ver_1/xxx/132","myBrandList":"<brandlist count=\"0\" ver=\"706590051\"></brandlist>","customizedInfo":{"brand_flag":0},"headImgMd5":"7eac7bae5c4699b9e8144afb982ea2be","encryptUserName":"v3_020b3826fd030100000000002bc2091c073a78000000501ea9a3dba12f95f6b60a0536a1adb632e80122c59af9d83c544819c6c8f79b2efb48535619d714a85262e8075a629fb4af99d2be8fced109060c3b79ea98bf841bf523788e90d50c49221962@stranger","additionalContactList":{"item":{}},"chatroomVersion":0,"deleteFlag":0,"description":"ID：似水流年","labelIdlist":"13","phoneNumListInfo":{"count":1,"phoneNumList":[{"phoneNum":"131xxx"}]},"extFlag":0}],"ret":"AA=="},"Text":""}
        """
        if not wxid:
            return False
        api = '/friend/GetContactDetailsList'
        body = {"RoomWxIDList": [g_wxid], "UserNames": [wxid]}
        return self._api_call('POST', api, body, 'VP_FRD')

    def get_friend_relation(self, wxid):
        """
        获取好友关系
        :param wxid: 联系人wxid
        :return: json - Data.FriendRelation=0 代表好友
        {"Code":200,"Data":{"Openid":"xxx ","NickName":"6L6e","HeadImgUrl":"http://wx.qlogo.cn/mmopen/xxx/0","Sign":"ff030fd02c35e770fef7224cc502ee78146b811e","FriendRelation":0},"Text":""}
        """
        if not wxid:
            return False
        api = '/friend/GetFriendRelation'
        body = {"UserName": wxid}
        return self._api_call('POST', api, body, 'VP_FRD')

    def get_label_list(self):
        """
        获取标签列表
        :return: json - Data.labelPairList.0.labelName
        {"Code":200,"Data":{"labelCount":14,"labelPairList":[{"labelName":"xxx","labelId":2}]},"Text":""}
        """
        api = '/label/GetContactLabelList'
        return self._api_call('GET', api, None, 'VP_FRD')


