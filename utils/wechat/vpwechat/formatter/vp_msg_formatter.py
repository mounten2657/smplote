import random
from xml.etree import ElementTree
from service.wechat.callback.vp_command_service import VpCommandService
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
            "msg_time": '',
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
        o_msg_id = message.get('msg_id', 0)
        p_msg_id = message.get('new_msg_id', o_msg_id)
        msg_time = Time.dft(message.get('create_time', 0))
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
            if self.g_wxid and self.g_wxid in self.a_g_wxid:  # 红包提醒
                title = "【红包提醒】"
                des = f"[%s_wxid_name% {Time.date('%H:%M')} 发送红包]\r\n"
                des += f"[@艾特位招租]"
                commander = VpCommandService(self.app_key, self.g_wxid, send_wxid)
                commander.vp_card_msg(title, des)
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
            if any(prefix in u_content[:40] for prefix in ('&lt;?xml', '<?xml', '&lt;msg', '<msg')):
                u_content = Str.html_unescape(u_content)
                c_type, c_link = self.get_content_data(u_content)
                if Attr.get(c_link, 'title'):  # 多重引用
                    u_content_str = f"[{str(c_type).upper()}][{c_link['title']}]"
                    if Attr.get(c_link, 'des'):
                        u_content_str += f"({c_link['des']})"
                else:  # 复杂引用
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
        elif 'invited' == content_type:  # 邀请
            self.g_wxid = s_wxid if has_sender else self.g_wxid
            s_wxid = content_link['u_wxid']
            t_wxid = content_link['i_wxid']
            f_wxid = self.g_wxid if self.g_wxid else s_wxid
            self.is_my_protect = 0
            s_name, t_name, f_name = self.extract_user_name(self.g_wxid, s_wxid, t_wxid, 0, client)
            t_name = t_name if t_name != t_wxid else content_link['i_name']
            self.msg['send_wxid_name'], self.msg['to_wxid_name'], self.msg['from_wxid_name'] = s_name, t_name, f_name
            send_wxid, content = [s_wxid, f"[邀请消息] {s_name} 邀请 {t_name} 加入了群聊"]
            if self.g_wxid and self.g_wxid in self.a_g_wxid:  # 邀请消息
                welcome_list = [
                    "欢迎新成员！祝玩好玩嗨玩出下一代，群里永远有你的快乐位置～",
                    "热烈欢迎！咱群个个都是人才，说话又好听，来了的都不想走，以后多唠多互动呀～",
                    "新成员入群啦！温馨提示：爆照极有可能触发群主发对象流程，快准备好你的美照帅照吧～",
                    "欢迎新朋友！进群就是一家人，跑图有人陪，emo有人哄，福利还能一起冲～",
                    "热烈欢迎新伙伴！群里没有冷场，只有唠不完的梗和等你一起蹭的图，快融入我们吧～",
                    "新成员来啦！祝在群里早日找到合拍CP，每天都有好心情，群主的红包也不会少～",
                    "欢迎加入大家庭！这里没有孤单，只有一群有趣的人陪你聊日常、闯快乐，以后多指教～",
                    "新伙伴入群欢迎！进群即享：陪跑图不被丢，蹭福利不落后，还有一群逗比陪你走～",
                    "欢迎新成员！愿你在群里每天都有新快乐，想吃肯德基有人约，想吐槽有人听～",
                    "热烈欢迎新朋友！咱群主打一个温暖热闹，有困难大家帮，有快乐一起享，期待你的精彩～",
                    "新成员来啦！祝在群里玩得尽兴，聊得开心，不管是唠嗑还是蹭图，都能找到同频的人～",
                    "欢迎加入！进群就是缘分，以后一起分享日常，互蹭福利，群主的冷笑话也会按时送达哦～",
                    "热烈欢迎新伙伴！群里藏着超多有趣灵魂，等你一起唠梗、跑图、盼福利，来了就别想走～",
                    "欢迎新成员！愿你在群里收获快乐，结交好友，每天都能被温暖和笑声包围～",
                    "新伙伴入群欢迎！进群福利已就位：陪聊、陪玩、陪吐槽，还有不定期惊喜，快开启你的群聊时光～"
                ]
                welcome = random.choice(welcome_list)
                title = "【欢迎新成员】"
                des = f"昵称：{t_name}\r\n"
                des += f"时间：{Time.date()}"
                commander = VpCommandService(self.app_key, self.g_wxid, send_wxid)
                commander.vp_card_msg(title, des)
                commander.vp_normal_msg(welcome, [{"wxid": t_wxid, "nickname": t_name}])
            client.refresh_room(self.g_wxid)
        elif 'revoke' == content_type:  # 撤回
            s_name, t_name, f_name = self.extract_user_name(self.g_wxid, s_wxid, t_wxid, self.is_my_protect, client)
            title_str = Str.extract_xml_attr(content_text, 'replacemsg').split('撤回', 1)
            content_link['title'] = f"{s_name} 撤回{title_str[1]}"
            send_wxid, content = [s_wxid, f"[撤回消息] {content_link['title']}"]
        elif 'song' == content_type:  # 点歌
            send_wxid, content = [s_wxid, f"[点歌消息] {content_link['title']}-{content_link['des']}.mp3"]
        elif 'share' == content_type:  # 分享
            s_title = content_link['title']
            if content_link['des']:
                s_title += f" | {content_link['des']}"
            send_wxid, content = [s_wxid, f"[分享消息] [{s_title}]({content_link['url']})"]
        elif 'gift' == content_type:  # 礼物
            send_wxid, content = [s_wxid, f"[礼物消息] [{content_link['skutitle']}]({content_link['url']})"]
        elif 'call' == content_type:  # 通话
            send_wxid, content = [s_wxid, f"[通话消息] [{p_msg_id}.{content_type}]"]
        elif 'location' == content_type:  # 位置
            send_wxid, content = [s_wxid, f"[位置消息] [{content_link['label']} {content_link['poiname']}]({content_link['x']}, {content_link['y']})"]
        elif 'location_share' == content_type:  # 位置共享
            send_wxid, content = [s_wxid, f"[位置共享消息] {content_link['title']}"]
        elif 'location_share_data' == content_type:  # 位置共享数据
            send_wxid, content = [s_wxid, '']
        elif 'wx_app' == content_type:  # 应用
            send_wxid, content = [s_wxid, f"[应用消息] [{content_link['title']}{content_link['des']}]({content_link['url']})"]
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
        self.msg.update({
            "msg_id": message.get('new_msg_id', 0),
            "msg_type": message.get('msg_type', 0),
            "send_wxid": send_wxid if send_wxid else f_wxid,
            "to_wxid": t_wxid,
            "from_wxid": f_wxid,
            "content": content,
            "content_type": content_type,
            "content_link": content_link,
            "p_msg_id": o_msg_id,
            "msg_time": msg_time,
            "app_key": self.app_key,
            "self_wxid": self.self_wxid,
            "is_my": self.is_my,
            "is_sl": self.is_sl,
            "is_group": int(bool(self.g_wxid)),
            "g_wxid": self.g_wxid,
        })

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
        elif all(key in content_text for key in ('sysmsg', '加入', '群聊')):  # 邀请 - "{g_wxid}:\n{<invited_xml>}"
            # "$username$"邀请"$names$"加入了群聊
            # "$adder$"通过扫描"$from$"分享的二维码加入群聊
            content_type = 'invited'
            content_link = {
                "template": Str.extract_xml_attr(content_text, 'template'),
                "u_wxid": Str.extract_xml_attr(content_text, 'username', 1),
                "u_name": Str.extract_xml_attr(content_text, 'nickname', 1).replace('\\', ''),
                "i_wxid": Str.extract_xml_attr(content_text, 'username', 2),
                "i_name": Str.extract_xml_attr(content_text, 'nickname', 2).replace('\\', ''),
            }
        elif all(key in content_text for key in ('msg', 'emoji', 'cdnurl')):  # 表情 - "{s_wxid}:\n{<emoji_xml>}"
            content_type = 'gif'
            # 仅保存下载链接，先不进行下载
            content_link = {
                "type": 3001,
                "url": Str.extract_attr(content_text, 'cdnurl').replace('&amp;', '&'),
                "md5": Str.extract_attr(content_text, 'md5'),
            }
        elif all(key in content_text for key in ('msg', 'emojiinfo', 'cdnthumbaeskey', 'cdnthumburl')):  # 表情 - "{s_wxid}:\n{<emoji_xml>}"
            content_type = 'gif'
            # 仅保存下载链接，先不进行下载
            content_link = {
                "type": 3,
                "aes_key": Str.extract_xml_attr(content_text, 'cdnthumbaeskey'),
                "url": Str.extract_xml_attr(content_text, 'cdnthumburl'),
                "md5": Str.extract_xml_attr(content_text, 'emoticonmd5'),
            }
        elif all(key in content_text for key in ('msg', 'img', 'aeskey', 'cdnmidimgurl')):  # 图片 - "{s_wxid}:\n{<image_xml>}"
            content_type = 'png'
            # 仅保存md5，先不进行下载
            content_link = {
                "aes_key": Str.extract_attr(content_text, 'aeskey'),
                "url": Str.extract_attr(content_text, 'cdnmidimgurl'),
                "md5": Str.extract_attr(content_text, 'md5'),
            }
        elif all(key in content_text for key in ('xml', 'videomsg', 'aeskey', 'cdnvideourl')):  # 视频 - "{s_wxid}:\n<video_xml>}"
            content_type = 'mp4'
            # 仅保存md5，先不进行下载
            content_link = {
                "aes_key": Str.extract_attr(content_text, 'aeskey'),
                "url": Str.extract_attr(content_text, 'cdnvideourl'),
                "md5": Str.extract_attr(content_text, 'md5'),
            }
        elif all(key in content_text for key in ('appmsg', 'title', 'fileuploadtoken', 'fileext')):  # 文件 - "{s_wxid}:\n{<file_xml>}"
            content_type = 'file'
            # 仅保存md5，先不进行下载
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "file_ext": Str.extract_xml_attr(content_text, 'fileext'),
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
            # 仅保存c_msg_id，先不进行下载
            content_link = {
                "aes_key": Str.extract_attr(content_text, 'aeskey'),
                "url": Str.extract_attr(content_text, 'voiceurl'),
                "md5": Str.extract_attr(content_text, 'voicemd5'),
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
        elif all(key in content_text for key in ('appmsg', 'title', 'url', 'gift', '微信礼物')):  # 礼物 - "{s_wxid}:\n{<gift_xml>}"
            content_type = 'gift'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "des": Str.extract_xml_attr(content_text, 'des'),
                "url": Str.extract_xml_attr(content_text, 'url').replace('&amp;', '&'),
                "skutitle": Str.extract_xml_attr(content_text, 'skutitle'),
                "presentcntwording": Str.extract_xml_attr(content_text, 'presentcntwording'),
                "fromusername": Str.extract_xml_attr(content_text, 'fromusername'),
            }
        elif all(key in content_text for key in ('sysmsg', 'voipmt')):  # 通话 - "{s_wxid}:\n{<call_xml>}"
            content_type = 'call'
            content_link = {
                "banner": Str.extract_xml_attr(content_text, 'banner'),
                "invite": Str.extract_xml_attr(content_text, 'invite'),
            }
        elif all(key in content_text for key in ('msg', 'location', 'label')):  # 位置 - "{s_wxid}:\n{<location_xml>}"
            content_type = 'location'
            content_link = {
                "label": Str.extract_attr(content_text, 'label'),
                "x": Str.extract_attr(content_text, 'x'),
                "y": Str.extract_attr(content_text, 'y'),
                "poiname": Str.extract_attr(content_text, 'poiname'),
            }
        elif '位置共享' in content_text:
            if '结束' in content_text:
                content_type = 'location_share'
                content_link = {"tag": "LS_END", "title": "位置共享已结束"}
            elif '发起' in content_text:
                content_type = 'location_share'
                content_link = {"tag": "LS_START", "title": "发起了位置共享"}
            else:
                content_type = 'unknown'
                content_link = {}
        elif any(key in content_text for key in ('talkroominfo', 'trackmsg')):  # 位置共享数据 - "{s_wxid}:\n{<lsd_xml>}"
            # 太多了不要
            content_type = 'location_share_data'
            content_link = {}
        elif all(key in content_text for key in ('appmsg', 'title')):  # 应用 - "{s_wxid}:\n{<app_xml>}"
            # 基本都是未识别的 xml
            content_type = 'wx_app'
            content_link = {
                "title": Str.extract_xml_attr(content_text, 'title'),
                "des": Str.extract_xml_attr(content_text, 'des'),
                "url": Str.extract_xml_attr(content_text, 'url').replace('&amp;', '&'),
                "fromusername": Str.extract_xml_attr(content_text, 'fromusername'),
            }
            nickname = Str.extract_xml_attr(content_text, 'nickname')
            desc = Str.extract_xml_attr(content_text, 'desc')
            url = Str.extract_xml_attr(content_text, 'url', 2).replace('&amp;', '&')
            if nickname and desc:
                content_link['title'], content_link['des'], content_link['url'] = nickname, desc, url
            if not content_link['url']:
                content_link['url'] = Str.extract_xml_attr(content_text, 'tpurl').replace('&amp;', '&')
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
        # is_at = 1 if '在群聊中@了你' in push_content else 0
        is_at = 1 if at_user else 0
        self.msg.update({
            "at_user": at_user,
            "is_at": is_at,
        })
        return self.msg

    def handler_nickname(self, client):
        """处理昵称"""
        if self.msg.get('send_wxid_name') and self.msg.get('to_wxid_name') and self.msg.get('from_wxid_name'):
            return self.msg
        self.msg['send_wxid_name'], self.msg['to_wxid_name'], self.msg['from_wxid_name'] \
            = self.extract_user_name(self.g_wxid, self.msg['send_wxid'], self.msg['to_wxid'], self.is_my_protect, client)
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
            at_user = at_user_node.text if at_user_node is not None else ''
            return at_user if at_user else ''
        except ElementTree.ParseError:
            return ''
