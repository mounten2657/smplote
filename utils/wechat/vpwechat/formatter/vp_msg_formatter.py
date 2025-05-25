from xml.etree import ElementTree
from utils.wechat.vpwechat.factory.vp_base_factory import VpBaseFactory
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Logger, Attr, Str, Time

logger = Logger


class VpMsgFormatter(VpBaseFactory):
    """Vp 消息格式器"""

    def __init__(self, app_key=None):
        super().__init__(app_key)
        self.is_my = None
        self.is_sl = None
        self.has_sender = None
        self.g_wxid = None
        self.is_my_protect = None
        # 消息结构预览
        self.msg = {
            "msg_id": 0,
            "msg_type": 0,
            "from_wxid": '',
            "from_wxid_name": '',
            "to_wxid": '',
            "to_wxid_name": '',
            "send_wxid": '',
            "send_wxid_name": '',
            "content": '',
            "content_type": '',
            "content_link": '',
            "p_msg_id": 0,
            "app_key": '',
            "self_wxid": '',
            "is_my": 0,
            "is_sl": 0,
            "is_group": 0,
            "g_wxid": '',
            "at_user": '',
            "is_at": 0,
        }

    def context(self, params):
        """消息格式化"""
        message = params['message']
        contents = message.get('content', {}).get('str', '')
        client = VpClient(self.app_key)
        self.is_my = params['is_my']
        self.is_my_protect = self.is_my
        self.is_sl = params['is_sl']
        self.has_sender = ':\n' in contents[:32]
        self.g_wxid = params['g_wxid']
        # 消息分发处理
        self.msg = self.dispatch(message, client)
        # 处理at
        self.msg = self.handler_at_user(message)
        # 处理昵称
        self.msg = self.handler_nickname(client)
        return self.msg

    def dispatch(self, message, client):
        """消息分类处理"""
        contents = message.get('content', {}).get('str', '')
        p_msg_id = message.get('new_msg_id', message.get('msg_id', 0))
        f_wxid = message.get('from_user_name', {}).get('str', '')
        t_wxid = message.get('to_user_name', {}).get('str', '')
        has_sender = self.has_sender

        # 尝试解析通用格式 - "{s_wxid}:\n{<xml_content>}"
        if has_sender:
            s_wxid, content_text = str(contents).split(':\n', 1)
        else:
            s_wxid, content_text = [f_wxid, contents]

        # 获取消息类型
        content_type, content_link = self.get_content_data(content_text)
        if 'gif' == content_type:  # 表情
            send_wxid, content = [s_wxid, f"[表情消息] {p_msg_id}.{content_type}"]
        elif 'png' == content_type:  # 图片
            send_wxid, content = [s_wxid, f"[图片消息] {p_msg_id}.{content_type}"]
        elif 'mp4' == content_type:  #
            send_wxid, content = [s_wxid, f"[视频消息] {p_msg_id}.{content_type}"]
        elif 'file' == content_type:  # 文件
            if 'FILE_END' != content_link['tag']:
                send_wxid, content = [s_wxid, '']  # 文件传输的开始，内容置为空
            else:
                send_wxid, content = [s_wxid, f"[文件消息] {content_link['title']}"]  # 文件传输结束
        elif 'voice' == content_type:  # 语音
            send_wxid, content = [s_wxid, f"[语音消息] {p_msg_id}.{content_type}"]
        elif 'red' == content_type:  # 红包
            send_wxid, content = [s_wxid, f"[红包消息] [{content_link['title']}-{content_link['sender_title']}]"]
        elif 'transfer' == content_type:  # 转账
            s_wxid = content_link['payer_username']
            t_wxid = content_link['receiver_username']
            f_wxid = self.g_wxid if self.g_wxid else s_wxid
            self.is_my_protect = 0
            s_name, t_name, f_name = self.extract_user_name(self.g_wxid, s_wxid, t_wxid, 0, client)
            content_str = f"[转账消息] [{content_link['title']}-{content_link['pay_memo']}-{content_link['fee_desc']}]"
            send_str = f"({s_name} 转给 {t_name})" if has_sender else f"({t_name} 已收款)"
            send_wxid, content = [s_wxid, f"{content_str}{send_str}"]
        elif 'transfer_invalid' == content_type:  # 转账到期提醒
            s_name, t_name, f_name = self.extract_user_name(self.g_wxid, s_wxid, t_wxid, self.is_my_protect, client)
            title_str = Str.extract_xml_attr(content_text, 'content').split('有', 1)
            content_link['title'] = Str.remove_html_tags(f"{t_name} 有{title_str[1]}")
            send_wxid, content = [s_wxid, f"[转账到期消息] {content_link['title']}"]
        elif 'transfer_back' == content_type:  # 转账退回提醒
            send_wxid, content = [s_wxid, f"[转账退回消息] 转账已自动退回，交易流水号[{content_link['pay_msg_id']}]"]  # 用假的
        elif 'mini' == content_type:  # 小程序
            content_str = f"[小程序消息] [{content_link['source_nickname']}-{content_link['title']}]({content_link['url']})"
            send_wxid, content = [s_wxid, content_str]
        elif 'join' == content_type:  # 接龙
            send_wxid, content = [s_wxid, f"[接龙消息] {content_link['title']}"]
        elif 'quote' == content_type:  # 引用
            u_content = content_link['u_content']
            # 判断是否多重引用
            if any(u_content.startswith(prefix) for prefix in ('&lt;?xml', '<?xml', '&lt;msg', '<msg')):
                u_content = Str.html_unescape(u_content)
                u_content_str = Str.extract_xml_attr(u_content, 'title')
                if not u_content_str:  # 复杂引用
                    c_type, c_link = self.get_content_data(u_content)
                    p_svr_id = content_link.get('p_new_msg_id')
                    u_content_str = f"[{str(c_type).upper()}] {p_svr_id if p_svr_id else p_msg_id}.{c_type}"
                content_link['u_content'] = u_content_str
            send_wxid, content = [s_wxid, f"[引用消息] {content_link['u_name']}: {content_link['u_content']}\n----------\n{content_link['title']}"]
        elif 'pat' == content_type:  # 拍一拍
            self.g_wxid = s_wxid if has_sender else self.g_wxid
            s_wxid = content_link['from_username']
            t_wxid = content_link['patted_username']
            f_wxid = self.g_wxid if self.g_wxid else s_wxid
            self.is_my_protect = 0
            s_name, t_name, f_name = self.extract_user_name(self.g_wxid, s_wxid, t_wxid, 0, client)
            send_wxid, content = [s_wxid, f"[拍一拍消息] {s_name} 拍了拍 {t_name} {content_link['pat_suffix']}"]
        elif 'revoke' == content_type:  # 撤回
            s_name, t_name, f_name = self.extract_user_name(self.g_wxid, s_wxid, t_wxid, self.is_my_protect, client)
            title_str = Str.extract_xml_attr(content_text, 'replacemsg').split('撤回', 1)
            content_link['title'] = f"{s_name} 撤回{title_str[1]}"
            send_wxid, content = [s_wxid, f"[撤回消息] {content_link['title']}"]
        elif 'song' == content_type:  # 点歌
            send_wxid, content = [s_wxid, f"[点歌消息] {content_link['title']}-{content_link['des']}.mp3"]
        elif 'share' == content_type:  # 分享
            send_wxid, content = [s_wxid, f"[分享消息] [{content_link['title']}]({content_link['url']})"]
        elif self.is_my or self.is_sl:  # 自己的消息 或 私聊消息 - "{content}"
            content_type = 'text'
            content_link = {}
            send_wxid, content = [s_wxid, str(content_text).strip()]
        elif self.has_sender:  # 普通消息 - "{s_wxid}:\n{content}"
            content_type = 'text'
            content_link = {}
            send_wxid, content = [s_wxid, content_text]
        else:  # 未识别 - 不放行
            content_type = 'unknown'
            content_link = {}
            send_wxid, content = [s_wxid, '']

        # 更新消息数据
        self.msg = {
            "msg_id": message.get('new_msg_id', 0),
            "msg_type": message.get('msg_type', 0),
            "send_wxid": send_wxid if send_wxid else f_wxid,
            "to_wxid": t_wxid,
            "from_wxid": f_wxid,
            "content": content,
            "content_type": content_type,
            "content_link": content_link,
            "p_msg_id": p_msg_id,
            "app_key": self.app_key,
            "self_wxid": self.self_wxid,
            "is_my": self.is_my,
            "is_sl": self.is_sl,
            "is_group": int(bool(self.g_wxid)),
            "g_wxid": self.g_wxid,
        }

        return self.msg

    def get_content_data(self, content_text):
        """解析消息内容"""
        if all(key in content_text for key in ('appmsg', 'title', 'svrid', 'displayname', 'content')):  # 引用 - "{s_wxid}:\n{<yy_xml>}"
            # 引用消息优先 - 因为它可能包含所有类型的消息
            content_type = 'quote'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "p_new_msg_id": Str.extract_xml_attr(content_text, 'svrid'),  # 源消息的 new_msg_id
                "u_wxid": Str.extract_xml_attr(content_text, 'chatusr'),
                "u_name": Str.extract_xml_attr(content_text, 'displayname'),
                "u_content": Str.extract_xml_attr(content_text, 'content'),
            }
        elif all(key in content_text for key in ('msg', 'emoji', 'cdnurl')):  # 表情 - "{s_wxid}:\n{<emoji_xml>}"
            content_type = 'gif'
            # 仅保存下载链接，不进行下载
            content_link = {
                "url": Str.extract_attr(content_text, 'cdnurl').replace('&amp;', '&'),
                "md5": Str.extract_attr(content_text, 'md5'),
            }
        elif all(key in content_text for key in ('msg', 'img', 'aeskey', 'cdnmidimgurl')):  # 图片 - "{s_wxid}:\n{<image_xml>}"
            content_type = 'png'
            # 下载链接暂时还没有研究出来，先贴上  aeskey 和 cdnmidimgurl
            content_link = {
                "aes_key": Str.extract_attr(content_text, 'aeskey'),
                "url": Str.extract_attr(content_text, 'cdnmidimgurl'),
                "md5": Str.extract_attr(content_text, 'md5'),
            }
        elif all(key in content_text for key in ('xml', 'videomsg', 'aeskey', 'cdnvideourl')):  # 视频 - "{s_wxid}:\n<video_xml>}"
            content_type = 'mp4'
            # 下载链接暂时还没有研究出来，先贴上  aeskey 和 cdnvideourl
            content_link = {
                "aes_key": Str.extract_attr(content_text, 'aeskey'),
                "url": Str.extract_attr(content_text, 'cdnvideourl'),
                "md5": Str.extract_attr(content_text, 'md5'),
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'fileuploadtoken', 'fileext')):  # 文件 - "{s_wxid}:\n{<file_xml>}"
            content_type = 'file'
            # 下载链接暂时还没有研究出来，先贴上  aeskey 和 cdnattachurl
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "fileext": Str.extract_xml_attr(content_text, 'fileext'),
                "md5": Str.extract_xml_attr(content_text, 'md5'),
                "tag": "FILE_START",
            }
            # 文件传输有两条信息（开始和结束），现在只接收文件传输完成的消息
            if all(key in content_text for key in ('cdnattachurl', 'aeskey')):
                # 下载链接暂时还没有研究出来，先贴上  aeskey 和 cdnattachurl
                content_link.update({
                    "aes_key": Str.extract_xml_attr(content_text, 'aeskey'),
                    "url": Str.extract_xml_attr(content_text, 'cdnattachurl'),
                    "tag": "FILE_END",
                })
        elif all(key in content_text for key in ('voicemsg', 'aeskey', 'voiceurl', 'clientmsgid')):  # 语音 - "{s_wxid}:\n{<voice_xml>}"
            content_type = 'voice'
            content_link = {
                "aes_key": Str.extract_attr(content_text, 'aeskey'),
                "url": Str.extract_attr(content_text, 'voiceurl'),
                "client_msg_id": Str.extract_attr(content_text, 'clientmsgid'),
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'sendertitle', 'nativeurl', 'templateid', 'iconurl')):  # 红包 - "{s_wxid}:\n{<red_xml>}"
            content_type = 'red'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "sender_title": Str.extract_xml_attr(content_text, 'sendertitle'),
                "native_url": Str.extract_xml_attr(content_text, 'nativeurl'),
                "icon_url": Str.extract_xml_attr(content_text, 'iconurl'),
                "template_id": Str.extract_xml_attr(content_text, 'templateid'),
                "invalid_time": Str.extract_xml_attr(content_text, 'invalidtime'),
            }
            content_link['invalid_date'] = Time.dft(int(content_link['invalid_time']) if content_link['invalid_time'] else 0)
        elif all(key in content_text for key in ('appmsg', 'title', 'feedesc', 'pay_memo',
                                                 'receiver_username', 'payer_username')):  # 转账 - "{s_wxid}:\n{<transfer_xml>}" || "{<transfer_xml>"
            content_type = 'transfer'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "pay_memo": Str.extract_xml_attr(content_text, 'pay_memo'),
                "fee_desc": Str.extract_xml_attr(content_text, 'feedesc'),
                "payer_username": Str.extract_xml_attr(content_text, 'payer_username'),
                "receiver_username": Str.extract_xml_attr(content_text, 'receiver_username'),
                "tc_id": Str.extract_xml_attr(content_text, 'transcationid'),
                "tid": Str.extract_xml_attr(content_text, 'transferid'),
                "invalid_time": Str.extract_xml_attr(content_text, 'invalidtime'),
            }
            content_link['invalid_date'] = Time.dft(int(content_link['invalid_time']) if content_link['invalid_time'] else 0)
        elif all(key in content_text for key in ('sysmsg', '待', '转账', '过期')):  # 转账到期提醒 - "{g_wxid}:\n{<transfer_invalid_xml>}"
            content_type = 'transfer_invalid'
            content_link = {
                "title": '',
                "url": Str.extract_attr(content_text, 'href'),
                "tid": Str.extract_xml_attr(content_text, 'transferid'),
            }
        elif all(key in content_text for key in ('sysmsg', 'PayMsgType', 'paymsgid', 'transferid')):  # 转账退回提醒 - "{s_wxid}:\n{<transfer_back_xml>}"
            content_type = 'transfer_back'
            content_link = {
                "PayMsgType": Str.extract_xml_attr(content_text, 'PayMsgType'),  # 25 退回
                "from_username": Str.extract_xml_attr(content_text, 'fromusername'),
                "to_username": Str.extract_xml_attr(content_text, 'tousername'),
                "pay_msg_id": Str.extract_xml_attr(content_text, 'paymsgid'),
                "tid": Str.extract_xml_attr(content_text, 'transferid'),
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'url', 'sourceusername', 'sourcedisplayname',
                                                 'weappiconurl', 'weapppagethumbrawurl')):  # 小程序 - "{s_wxid}:\n{<mini_xml>}"
            content_type = 'mini'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "url": Str.extract_xml_attr(content_text, 'url').replace('&amp;', '&'),
                "source_wxid": Str.extract_xml_attr(content_text, 'sourceusername'),
                "source_nickname": Str.extract_xml_attr(content_text, 'sourcedisplayname'),
                "icon_url": Str.extract_xml_attr(content_text, 'weappiconurl'),
                "cover_url": Str.extract_xml_attr(content_text, 'weapppagethumbrawurl'),
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'solitaire_info')):  # 接龙 - "{s_wxid}:\n{<join_xml>}"
            content_type = 'join'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "join_info": Str.extract_xml_attr(content_text, 'solitaire_info'),
            }
        elif all(key in content_text for key in ('sysmsg', 'fromusername', 'pattedusername',
                                                 'patsuffix', 'template')):  # 拍一拍 - "{g_wxid}:\n{<pat_xml>}" || "{<pat_xml>}"
            content_type = 'pat'
            content_link = {
                "from_username": Str.extract_xml_attr(content_text, 'fromusername'),
                "patted_username": Str.extract_xml_attr(content_text, 'pattedusername'),
                "pat_suffix": Str.extract_xml_attr(content_text, 'patsuffix'),
                "template": Str.extract_xml_attr(content_text, 'template'),
            }
        elif all(key in content_text for key in ('sysmsg', 'newmsgid', 'revokemsg', 'replacemsg')):  # 撤回 - "{s_wxid}:\n{<revoke_xml>}"
            content_type = 'revoke'
            content_link = {
                "msg_id": Str.extract_xml_attr(content_text, 'msgid'),
                "p_new_msg_id": Str.extract_xml_attr(content_text, 'newmsgid'),
                "title": '',
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'des', 'dataurl', 'songalbumurl','songlyric', 'appname')):  # 点歌 - "{s_wxid}:\n{<song_xml>}"
            content_type = 'song'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "des": Str.extract_xml_attr(content_text, 'des'),
                "data_url": Str.extract_xml_attr(content_text, 'dataurl').replace('&amp;', '&'),
                "img_url": Str.extract_xml_attr(content_text, 'songalbumurl'),
                "song_lyric": Str.extract_xml_attr(content_text, 'songlyric'),
                "appname": Str.extract_xml_attr(content_text, 'appname'),
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'url', 'webviewshared')):  # 分享 - "{s_wxid}:\n{<share_xml>}"
            content_type = 'share'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "des": Str.extract_xml_attr(content_text, 'des'),
                "url": Str.extract_xml_attr(content_text, 'url').replace('&amp;', '&'),
                "publisher_id": Str.extract_xml_attr(content_text, 'publisherId'),
                "publisher_req_id": Str.extract_xml_attr(content_text, 'publisherReqId'),
            }
        else:  # 未识别 - 不放行
            content_type = 'unknown'
            content_link = {}
        return content_type, content_link

    def handler_at_user(self, message):
        """处理at信息"""
        msg_source = message.get('msg_source', '')
        push_content = message.get('push_content', '')
        at_user = self.extract_at_user(msg_source)
        # is_at = 1 if self_wxid in str(at_user).split(',') else 0
        is_at = 1 if '在群聊中@了你' in push_content else 0
        self.msg.update({
            "at_user": at_user,
            "is_at": is_at,
        })
        return self.msg

    def handler_nickname(self, client):
        """处理昵称"""
        msg = self.msg
        msg['send_wxid_name'], msg['to_wxid_name'], msg['from_wxid_name'] \
            = self.extract_user_name(self.g_wxid, msg['send_wxid'], msg['to_wxid'], self.is_my_protect, client)
        self.msg = msg
        return self.msg

    @staticmethod
    def extract_user_name(g_wxid, s_wxid, t_wxid, is_my_protect, client):
        """提取成员昵称"""
        if g_wxid:  # 群聊 - 优先群备注名
            room = client.get_room(g_wxid)
            send_user = Attr.select_item_by_where(room['member_list'], {'wxid': s_wxid})
            to_user = Attr.select_item_by_where(room['member_list'], {'wxid': t_wxid})
            send_wxid_name = send_user.get('display_name', s_wxid) if send_user else s_wxid
            to_wxid_name = room.get('nickname', g_wxid) if is_my_protect else to_user.get('display_name', t_wxid) if to_user else t_wxid
            from_wxid_name = send_wxid_name if is_my_protect else room.get('nickname', g_wxid)
            if "@chatroom" in s_wxid:
                send_wxid_name = room.get('nickname', g_wxid)
        else:  # 私聊 - 优先备注名
            send_user = client.get_user(s_wxid)
            to_user = client.get_user(t_wxid)
            send_wxid_name = send_user.get('remark_name') if len(send_user.get('remark_name')) else send_user.get('nickname', s_wxid)
            to_wxid_name = to_user.get('remark_name') if len(to_user.get('remark_name')) else to_user.get('nickname', t_wxid)
            from_wxid_name = send_wxid_name
        return send_wxid_name, to_wxid_name, from_wxid_name

    @staticmethod
    def extract_at_user(msg_source):
        """提群被at的用户wxid"""
        try:
            root = ElementTree.fromstring(msg_source)
            at_user_node = root.find('atuserlist')
            return at_user_node.text if at_user_node is not None else ''
        except ElementTree.ParseError:
            return ''
