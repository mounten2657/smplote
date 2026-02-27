import os
from tool.core import Logger, Http, Time, Attr, File, Str
from service.vpp.vpp_serve_service import VppServeService
from model.wechat.wechat_api_log_model import WechatApiLogModel
from model.wechat.wechat_msg_model import WechatMsgModel

logger = Logger()


class VpClientFactory:

    def __init__(self, config, app_key):
        self.base_url = f"http://{config['ws_host']}:{config['ws_port']}"
        self.app_key = app_key
        self.key = config['app_list'][self.app_key]['token_key']

    def _api_call(self, method: str, uri: str, body: dict = None, biz_code: str = 'NULL', extra=None):
        """
        发起 wechatpad http 请求
        :param method:  http 请求方式
        :param uri:  请求路径
        :param body:  post 数据
        :param biz_code:  业务码
        :param extra:  额外参数
        :return: json
        """
        start_time = Time.now(0)
        url = f"{self.base_url}{uri}?key={self.key}"
        body.update({"app_key": self.app_key})
        logger.debug(f'VP API 请求参数:  {biz_code} - {method}[{uri}] - {body}', 'VP_API_CALL_STA')
        # 请求数据入库
        db = WechatApiLogModel()
        pid = db.add_log(self.app_key, method, uri, body, biz_code)
        # 执行接口请求
        method = 'JSON' if 'POST' == method else method
        res = Http.send_request(method, url, body)
        logger.debug(f'VP API 请求结果: {res}', 'VP_API_CALL_RET')
        # 更新执行结果
        run_time = round(Time.now(0) - start_time, 3) * 1000  # 执行时间单位为毫秒
        update_data = {"response_time": run_time, "response_result": res}
        if res.get('Code') == 200:
            update_data.update({"is_succeed": 1})
            self.insert_to_wechat_msg(res, biz_code, pid, extra)
        db.update_log(pid, update_data)
        return res

    def insert_to_wechat_msg(self, res, biz_code, lid, extra):
        """插入到微信消息表"""
        d0_mid = Attr.get_by_point(res, 'Data.newMsgId', 0)
        d1_mid = Attr.get_by_point(res, 'Data.0.resp.newMsgId', d0_mid)
        d2_mid = Attr.get_by_point(res, 'Data.0.resp.NewMsgId', d1_mid)
        msg_id = Attr.get_by_point(res, 'Data.0.resp.chat_send_ret_list.0.newMsgId', d2_mid)
        if 'VP_SMG' in biz_code and msg_id:
            mdb = WechatMsgModel()
            content = extra.get('content')
            c_type = extra.get('c_type')
            if not content or not c_type:
                return False
            if biz_code not in ['VP_SMG', 'VP_SMG_APP']:
                content = f"{content} {msg_id}.{c_type}"
            msg = {
                "msg_id": msg_id,
                "content": content,
                "content_type": c_type,
                "msg_time": Time.date(),
                "send_wxid": extra.get('self_wxid', ''),
                "send_wxid_name": extra.get('self_wxid_name', ''),
                "is_my": 1,
                "is_at": 0,
                "is_sl": 0,
                "is_group": 1,
                "msg_type": 4001,
                "app_key": self.app_key,
                "g_wxid": extra.get('g_wxid', ''),
                "g_wxid_name": extra.get('g_wxid_name', ''),
                "to_wxid": extra.get('g_wxid', ''),
                "to_wxid_name": extra.get('g_wxid_name', ''),
                "from_wxid": extra.get('self_wxid', ''),
                "from_wxid_name": extra.get('self_wxid_name', ''),
                "at_user": extra.get('at_user', ''),
                "p_msg_id": 0,
                "fid": extra.get('file', {}).get('id', 0),
                "pid": 0,
                "aid": extra.get('aid', 0),
                "lid": lid,
                "content_link": {},
            }
            mdb.add_msg(msg, self.app_key)
        return True

    def get_login_status(self):
        """
        获取在线状态
        :return: json - Data.loginState=1 代表在线
        {"Code":200,"Data":{"loginState":1,"expiryTime":"2026-05-17","loginErrMsg":"账号在线状态良好！","loginJournal":{"count":0,"logs":[]},"loginTime":"2025-05-17 05:38:56","onlineDays":0,"onlineTime":"本次在线: 0天0时7分","proxyUrl":"","targetIp":"223.152.206.237:8849","totalOnline":"总计在线: 0天0时8分"},"Text":""}
        """
        api = '/login/GetLoginStatus'
        return self._api_call('GET', api, {}, 'VP_LGS')

    def send_text_message(self, content, to_wxid, ats=None, extra=None):
        """
        发送文本消息
        :param content: 消息内容
        :param to_wxid: 接收者wxid
        :param ats: 需要 at 的人 - [{"wxid": "xxx", "nickname": "yyy"}]
        :param extra: 额外参数
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
            content = f"{at_str}\r\n{content}"
        body = {
            "MsgItem": [{
                "AtWxIDList": at_wxid_list,
                "ImageContent": "",
                "MsgType": 1,
                "TextContent": content,
                "ToUserName": to_wxid,

            }]
        }
        extra.update({"content": content, "c_type": "text", "at_user": ",".join(at_wxid_list)})
        return self._api_call('POST', api, body, 'VP_SMG', extra)

    def send_img_message(self, image_path, to_wxid, extra=None):
        """
        发送图片消息
        :param image_path: 图片本地路径，会转为 base64
        :param to_wxid: 接收者wxid
        :param extra: 额外参数
        :return:  json - Data.isSendSuccess
        {"Code":200,"Data":[{"isSendSuccess":true,"resp":{},"msgSource":"xml", "newMsgId":"xxx","toUSerName":"xxx"}],"Text":""}
        """
        if not image_path or not to_wxid:
            return False
        img_base64 = File.get_base64(image_path)
        api = '/message/SendImageNewMessage'
        body = {
            "MsgItem": [{
                "AtWxIDList": [],
                "ImageContent": img_base64,
                "MsgType": 2,
                "TextContent": "",
                "ToUserName": to_wxid,

            }]
        }
        extra.update({"content": "[图片消息]", "c_type": "png"})
        return self._api_call('POST', api, body, 'VP_SMG_IMG', extra)

    def send_voice_message(self, mp3_path, to_wxid, extra=None):
        """
        发送语音消息
        :param mp3_path: 图片本地路径，会转为 base64
        :param to_wxid: 接收者wxid
        :param extra: 额外参数
        :return:  json - Data.isSendSuccess
        {"Code":200,"Data":[{"isSendSuccess":true,"resp":{},"msgSource":"xml", "newMsgId":"xxx","toUSerName":"xxx"}],"Text":""}
        """
        if not mp3_path or not to_wxid:
            return False
        silk_path = VppServeService.mp3_to_silk(mp3_path)
        if not silk_path:
            return False
        silk_base64 = File.get_base64(silk_path)
        api = '/message/SendVoice'
        body = {
          "ToUserName": to_wxid,
          "VoiceData": silk_base64,
          "VoiceFormat": 1,
          "VoiceSecond": 0
        }
        extra.update({"content": "[语音消息]", "c_type": "voice"})
        return self._api_call('POST', api, body, 'VP_SMG_MP3', extra)

    def _send_app_message(self, xml, to_wxid, extra=None):
        """
        发送xml应用消息
        :param xml: xml结构内容
        :param to_wxid: 接收者wxid
        :param extra: 额外参数
        :return:  json - Data.isSendSuccess
        {"Code":200,"Data":[{"isSendSuccess":true,"resp":{},"msgSource":"xml", "newMsgId":"xxx","toUSerName":"xxx"}],"Text":""}
        """
        if not xml or not to_wxid:
            return False
        api = '/message/SendAppMessage'
        body = {
            "AppList": [
                {
                    "ContentType": 0,
                    "ContentXML": xml,
                    "ToUserName": to_wxid
                }
            ]
        }
        # extra.update({"content": "[应用消息]", "c_type": "app"})
        return self._api_call('POST', api, body, 'VP_SMG_APP', extra)

    def send_dg_message(self, res, to_wxid, extra=None):
        """
        发送点歌消息
        :param res: 歌曲信息
        :param to_wxid: 接收者wxid
        :param extra: 额外参数
        :return:  json - Data.isSendSuccess
        {"Code":200,"Data":[{"isSendSuccess":true,"resp":{},"msgSource":"xml", "newMsgId":"xxx","toUSerName":"xxx"}],"Text":""}
        """
        if not res or not to_wxid:
            return False
        try:
            if not res['song_url']:
                return ""
            eid = Str.base64_encode(res['id'])
            share_info = f"<musicShareItem><mvCoverUrl><![CDATA[]]></mvCoverUrl><mvSingerName><![CDATA[]]></mvSingerName><musicDuration>0</musicDuration><mid><![CDATA[{eid}]]></mid></musicShareItem>"
            xml = f"<appmsg appid='{res['appid']}' sdkver='0'>  <title>{res['name']}</title>  <des>{res['singer_name']}</des>  <type>76</type>  <url>{res['song_url']}</url>  <lowurl></lowurl>  <dataurl>{res['data_url']}</dataurl>  <lowdataurl></lowdataurl>  <songalbumurl>{res['album_img']}</songalbumurl>  <songlyric></songlyric> {share_info} <appattach>    <cdnthumbaeskey/>    <aeskey/>  </appattach></appmsg>"
        except Exception as e:
            xml = ''
        if not xml:
            return False
        extra.update({"content": f"[点歌消息] [{res['name']}-{res['singer_name']}.mp3]", "c_type": f"app_dg"})
        return self._send_app_message(xml, to_wxid, extra)

    def send_card_message(self, res, to_wxid, extra=None):
        """
        发送卡片消息
        :param res: 卡片信息
        :param to_wxid: 接收者wxid
        :param extra: 额外参数
        :return:  json - Data.isSendSuccess
        {"Code":200,"Data":[{"isSendSuccess":true,"resp":{},"msgSource":"xml", "newMsgId":"xxx","toUSerName":"xxx"}],"Text":""}
        """
        if not res or not to_wxid:
            return False
        try:
            if not res['title']:
                return ""
            xml = f"<appmsg appid='' sdkver='0'><title>{res['title']}</title><des>{res['des']}</des><type>5</type><url>{res['url']}</url><thumburl>{res['thumb']}</thumburl></appmsg>"
        except Exception as e:
            xml = ''
        if not xml:
            return False
        des = str(res['des']).split('\r\n')[0]
        extra.update({"content": f"[卡片消息] [{res['title']}]({des}).card", "c_type": f"app_card"})
        return self._send_app_message(xml, to_wxid, extra)

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

    def get_friend_info(self, wxid_list, g_wxid=''):
        """
        获取联系人详情
        :param wxid_list: 联系人wxid 列表
        :param g_wxid: 群聊wxid
        :return: json - Data.contactList.0.description
        {"Code":200,"Data":{"contactCount":1,"contactList":[{"userName":{"str":"wxid_xxx"},"nickName":{"str":"x"},"quanPin":{"str":"ci"},"sex":1,"remark":{"str":"🏅x"},"contactType":0,"province":"Offaly","signature":"花开花落花相似，人来人往人不同","hasWeiXinHdHeadImg":1,"alias":"weixinhao","snsUserInfo":{"sns_flag":1,"sns_bgimg_id":"http://szmmsns.qpic.cn/mmsns/xxx/0","sns_bgobject_id":14563952301353996000,"sns_flagex":7297,"sns_privacy_recent":72},"country":"IE","bigHeadImgUrl":"https://wx.qlogo.cn/mmhead/ver_1/xxx/0","smallHeadImgUrl":"https://wx.qlogo.cn/mmhead/ver_1/xxx/132","myBrandList":"<brandlist count=\"0\" ver=\"706590051\"></brandlist>","customizedInfo":{"brand_flag":0},"headImgMd5":"7eac7bae5c4699b9e8144afb982ea2be","encryptUserName":"v3_020b3826fd030100000000002bc2091c073a78000000501ea9a3dba12f95f6b60a0536a1adb632e80122c59af9d83c544819c6c8f79b2efb48535619d714a85262e8075a629fb4af99d2be8fced109060c3b79ea98bf841bf523788e90d50c49221962@stranger","additionalContactList":{"item":{}},"chatroomVersion":0,"deleteFlag":0,"description":"ID：似水流年","labelIdlist":"13","phoneNumListInfo":{"count":1,"phoneNumList":[{"phoneNum":"131xxx"}]},"extFlag":0}],"ret":"AA=="},"Text":""}
        """
        if not wxid_list:
            return False
        api = '/friend/GetContactDetailsList'
        body = {"RoomWxIDList": [g_wxid], "UserNames": wxid_list}
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
        return self._api_call('GET', api, {}, 'VP_FRD')

    def _get_file_path(self, message):
        """获取文件保存路径"""
        if int(message['is_sl']):
            if int(message['is_my']):
                f_wxid = message['to_wxid']
            else:
                f_wxid = message['send_wxid']
            fp = f"/friend/{str(f_wxid).replace('@', '__')}"
        else:
            fp = f"/room/{str(message['g_wxid']).split('@')[0]}"
            fp += f"/{Time.date('%Y%m')}"  # 群聊文件较多，按月存储
        if 'file' == message['content_type']:
            fp += f"/file/{message['content_link']['title']}"
        elif 'voice' == message['content_type']:
            fp += f"/mp3/{message['msg_id']}.silk"
        else:
            fp += f"/{message['content_type']}/{message['msg_id']}.{message['content_type']}"
        fk = File.enc_dir(fp)
        return fp, fk

    def download_file(self, message, is_retry = 0):
        """
        下载文件并返回文件基本信息（含可访问的文件链接）
        :param message: 标准消息结构体 - 来自队列表
        :param is_retry: 是否重试
        :return: json - 文件基本信息
        {'code': 0, 'msg': 'success', 'data': {'url': 'https://static.xxx.com/src/static/file/wechat/36/39/33/aZmc21aZH1VOWRNA0TXaZSPEWBHaZDFP14HFUC0HIFSLT.mp4', 'md5': 'b8aaa43ffefe1f35a7e44aed72df6431', 'size': 954061}}
        """
        if not message.get('content_type') or not message.get('content_link'):
            return {}
        file_type = {
            "GIF": 3001,
            "PNG": 2,
            "MP4": 4,
            "FILE": 5,
            "VOICE": 15,
        }
        try:
            start_time = Time.now(0)
            msg_type = str(message['content_type']).upper()
            biz_code = f"VP_{msg_type}"
            method = 'GRPC'
            uri = '/message/FileCdnDownload'
            fp, fk = self._get_file_path(message)
            content_link = message.get('content_link', {})
            fty = file_type[msg_type]
            if 'GIF' == msg_type:
                fty = content_link['type']
            body = {
                "fty": fty,
                "key": content_link.get('aes_key', msg_type),
                "url": content_link.get('url', ''),
                "fp": fp,
                "fk": fk,
                "fd": int(message.get('fd', 0))
            }
            logger.debug(f'VP GRPC 请求参数:  {biz_code} - {method}[{uri}] - {body}', 'VP_GRPC_CALL_STA')
            # 请求数据入库
            db = WechatApiLogModel()
            pid = db.add_log(self.app_key, method, uri, body, biz_code)
            # 使用 vpp 进行 cdn 下载
            if "PNG" == msg_type:  # 图片优先下载高清 - 1高清 | 2标准 | 3缩略
                body['fty'] = 1
                res = VppServeService.download_file(**body)
                if not Attr.get_by_point(res, 'data.url'):
                    body['fty'] = 2
                    res = VppServeService.download_file(**body)
            else:
                res = VppServeService.download_file(**body)
            logger.debug(f'VP GRPC 请求结果: {res}', 'VP_GRPC_CALL_RET')
            # 更新执行结果
            run_time = round(Time.now(0) - start_time, 3) * 1000
            update_data = {"response_time": run_time, "response_result": res}
            if Attr.get_by_point(res, 'data.url'):
                update_data.update({"is_succeed": 1})
            else:
                logger.warning(f'VP GRPC 请求异常: {res}', 'VP_GRPC_CALL_NUL')
            db.update_log(pid, update_data)
            data = res.get('data', {})
            data.update({
                "save_path": fp,
                "file_name": os.path.basename(fp),
                "fake_path": fk,
                "biz_code": biz_code,
            })
            return data
        except Exception as e:
            if not is_retry:
                # 提供一次重试机会
                logger.warning(f'VP GRPC 请求重试: {e}', 'VP_GRPC_CALL_RTY')
                Time.sleep(1)
                return self.download_file(message, 1)
            logger.error(f'VP GRPC 请求错误: {e}', 'VP_GRPC_CALL_ERR')
            return {}

    def wakeup_login(self):
        """
        唤醒登陆
        :return: 操作结果
        {"Code":200,"Data":{},"Text":""}
        """
        api = '/login/WakeUpLogin'
        body = {"Check": False, "Proxy": ""}
        return self._api_call('POST', api, body, 'VP_WKL')
