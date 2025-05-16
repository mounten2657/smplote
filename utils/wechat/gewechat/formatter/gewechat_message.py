import base64
import re
import uuid
import requests
import xml.etree.ElementTree as ET
from utils.wechat.gewechat.formatter.chat_message import ChatMessage
from utils.wechat.gewechat.bridge.context import ContextType
from tool.core import *

logger = Logger()


class GeWeChatMessage(ChatMessage):
    def __init__(self, msg, client):
        super().__init__(msg)
        self.msg = msg
        self.create_time = msg.get('Data', {}).get('CreateTime', 0)
        if not msg.get('Data'):
            logger.warning(f"[gewechat] Missing 'Data' in message")
            return
        if 'NewMsgId' not in msg['Data']:
            logger.warning(f"[gewechat] Missing 'NewMsgId' in message data")
            return
        self.msg_id = msg['Data']['NewMsgId']
        self.is_group = True if "@chatroom" in msg['Data']['FromUserName']['string'] else False

        notes_join_group = ["加入群聊", "加入了群聊", "invited", "joined"]  # 可通过添加对应语言的加入群聊通知中的关键词适配更多
        notes_bot_join_group = ["邀请你", "invited you", "You've joined", "你通过扫描"]

        self.client = client
        msg_type = msg['Data']['MsgType']

        conf = Config().gewechat_config()
        self.app_id = conf.get("gewechat_app_id")

        self.from_user_id = msg['Data']['FromUserName']['string']
        self.to_user_id = msg['Data']['ToUserName']['string']
        self.other_user_id = self.from_user_id

        # 检查是否是公众号等非用户账号的消息
        if self._is_non_user_message(msg['Data'].get('MsgSource', ''), self.from_user_id):
            self.ctype = ContextType.NON_USER_MSG
            self.content = msg['Data']['Content']['string']
            logger.debug(f"[gewechat] detected non-user message from {self.from_user_id}: {self.content}")
            return

        if msg_type == 1:  # Text message
            self.ctype = ContextType.TEXT
            self.content = msg['Data']['Content']['string']
        elif msg_type == 34:  # Voice message
            self.ctype = ContextType.VOICE
            if 'ImgBuf' in msg['Data'] and 'buffer' in msg['Data']['ImgBuf'] and msg['Data']['ImgBuf']['buffer']:
                silk_data = base64.b64decode(msg['Data']['ImgBuf']['buffer'])
                silk_file_name = f"voice_{str(uuid.uuid4())}.silk"
                silk_file_path = Dir.abs_dir('storage/tmp/') + silk_file_name
                with open(silk_file_path, "wb") as f:
                    f.write(silk_data)
                # TODO: silk2mp3
                self.content = silk_file_path
        elif msg_type == 3:  # Image message
            self.ctype = ContextType.IMAGE
            self.content = Dir.abs_dir('storage/tmp/') + str(self.msg_id) + ".png"
            self._prepare_fn = self.download_image
        elif msg_type == 49:  # 引用消息，小程序，公众号等
            # After getting content_xml
            content_xml = msg['Data']['Content']['string']
            # Find the position of '<?xml' declaration and remove any prefix
            xml_start = content_xml.find('<?xml version=')
            if xml_start != -1:
                content_xml = content_xml[xml_start:]
            # Now parse the cleaned XML
            root = ET.fromstring(content_xml)
            app_msg = root.find('appmsg')

            if app_msg is not None:
                msg_type = app_msg.find('type')
                if msg_type is not None and msg_type.text == '57':  # 引用消息
                    self.ctype = ContextType.TEXT
                    refer_msg = app_msg.find('refermsg')
                    if refer_msg is not None:
                        display_name = refer_msg.find('displayname').text
                        quoted_content = refer_msg.find('content').text
                        title = app_msg.find('title').text
                        self.content = f"「{display_name}: {quoted_content}」----------\n{title}"
                    else:
                        self.content = content_xml
                elif msg_type is not None and msg_type.text == '5':  # 可能是公众号文章
                    title = app_msg.find('title').text if app_msg.find('title') is not None else "无标题"
                    if "加入群聊" in title:
                        # 群聊邀请消息
                        self.ctype = ContextType.TEXT
                        self.content = content_xml
                    else:
                        # 公众号文章
                        self.ctype = ContextType.SHARING
                        url = app_msg.find('url').text if app_msg.find('url') is not None else ""
                        self.content = url

                else:  # 其他消息类型，暂时不解析，直接返回XML
                    self.ctype = ContextType.TEXT
                    self.content = content_xml
            else:
                self.ctype = ContextType.TEXT
                self.content = content_xml
        elif msg_type == 51:
            # msg_type = 51 表示状态同步消息，目前测试出来的情况有:
            # 1. 打开/退出某个聊天窗口
            # 是微信客户端的状态同步消息，可以忽略
            self.ctype = ContextType.STATUS_SYNC
            self.content = msg['Data']['Content']['string']
            return
        elif msg_type == 10002:  # Group System Message
            if self.is_group:
                content = msg['Data']['Content']['string']
                if any(note_bot_join_group in content for note_bot_join_group in notes_bot_join_group):  # 邀请机器人加入群聊
                    logger.warning("机器人加入群聊消息，不处理~")
                    pass
                elif any(note_join_group in content for note_join_group in
                         notes_join_group):  # 若有任何在notes_join_group列表中的字符串出现在NOTE中
                    try:
                        # Extract the XML part after the chatroom ID
                        xml_content = content.split(':\n', 1)[1] if ':\n' in content else content
                        root = ET.fromstring(xml_content)

                        # Navigate through the XML structure
                        sys_msg_template = root.find('.//sysmsgtemplate')
                        if sys_msg_template is not None:
                            content_template = sys_msg_template.find('.//content_template')
                            if content_template is not None and content_template.get('type') == 'tmpl_type_profile':
                                template = content_template.find('.//template')
                                if template is not None and '加入了群聊' in template.text:
                                    self.ctype = ContextType.JOIN_GROUP

                                    # Extract inviter info
                                    inviter_link = root.find(".//link[@name='username']//nickname")
                                    inviter_nickname = inviter_link.text if inviter_link is not None else "未知用户"

                                    # Extract invited member info
                                    invited_link = root.find(".//link[@name='names']//nickname")
                                    invited_nickname = invited_link.text if invited_link is not None else "未知用户"

                                    self.content = f'"{inviter_nickname}"邀请"{invited_nickname}"加入了群聊'
                                    self.actual_user_nickname = invited_nickname
                                    return

                    except ET.ParseError as e:
                        logger.error(f"[gewechat] Failed to parse group join XML: {e}")
                        # Fall back to regular content handling
                        pass
        elif msg_type == 47:
            self.ctype = ContextType.EMOJI
            self.content = msg['Data']['Content']['string']
        else:
            raise NotImplementedError("Unsupported message type: Type:{}".format(msg_type))

        # 获取群聊或好友的名称
        brief_info_response = self.client.get_brief_info(self.app_id, [self.other_user_id])
        if brief_info_response['ret'] == 200 and brief_info_response['data']:
            brief_info = brief_info_response['data'][0]
            self.other_user_nickname = brief_info.get('nickName', '')
            if not self.other_user_nickname:
                self.other_user_nickname = self.other_user_id

        if self.is_group:
            # 如果是群聊消息，获取实际发送者信息
            # 群聊信息结构
            """
            {
                "Data": {
                    "Content": {
                        "string": "wxid_xxx:\n@name msg_content" // 发送消息人的wxid和消息内容(包含@name)
                    }
                }
            }
            """
            # 获取实际发送者wxid
            self.actual_user_id = self.msg.get('Data', {}).get('Content', {}).get('string', '').split(':', 1)[
                0]  # 实际发送者ID
            # 从群成员列表中获取实际发送者信息
            """
            {
                "ret": 200,
                "msg": "操作成功",
                "data": {
                    "memberList": [
                        {
                            "wxid": "",
                            "nickName": "朝夕。",
                            "displayName": null,
                        },
                        {
                            "wxid": "",
                            "nickName": "G",
                            "displayName": "G1",
                        },
                    ]
                }
            }
            """
            chatroom_member_list_response = self.client.get_chatroom_member_list(self.app_id, self.from_user_id)
            if chatroom_member_list_response.get('ret', 0) == 200 and chatroom_member_list_response.get('data', {}).get(
                    'memberList', []):
                # 从群成员列表中匹配acual_user_id
                for member_info in chatroom_member_list_response['data']['memberList']:
                    if member_info['wxid'] == self.actual_user_id:
                        # 先获取displayName，如果displayName为空，再获取nickName
                        self.actual_user_nickname = member_info.get('displayName', '')
                        if not self.actual_user_nickname:
                            self.actual_user_nickname = member_info.get('nickName', '')
                        break
            # 如果actual_user_nickname为空，使用actual_user_id作为nickname
            if not self.actual_user_nickname:
                self.actual_user_nickname = self.actual_user_id

            # 检查是否被at
            # 群聊at结构
            """
            {
                'Data': {
                    'MsgSource': '<msgsource>\n\t<atuserlist><![CDATA[,wxid_xxx,wxid_xxx]]></atuserlist>\n\t<pua>1</pua>\n\t<silence>0</silence>\n\t<membercount>3</membercount>\n\t<signature>V1_cqxXBat9|v1_cqxXBat9</signature>\n\t<tmp_node>\n\t\t<publisher-id></publisher-id>\n\t</tmp_node>\n</msgsource>\n',
                },
            }
            """
            # 优先从MsgSource的XML中解析是否被at
            msg_source = self.msg.get('Data', {}).get('MsgSource', '')
            self.is_at = False
            xml_parsed = False
            if msg_source:
                try:
                    root = ET.fromstring(msg_source)
                    atuserlist_elem = root.find('atuserlist')
                    if atuserlist_elem is not None:
                        atuserlist = atuserlist_elem.text
                        self.is_at = self.to_user_id in atuserlist
                        xml_parsed = True
                        logger.debug(f"[gewechat] is_at: {self.is_at}. atuserlist: {atuserlist}")
                except ET.ParseError:
                    pass

            # 只有在XML解析失败时才从PushContent中判断
            if not xml_parsed:
                self.is_at = '在群聊中@了你' in self.msg.get('Data', {}).get('PushContent', '')
                logger.debug(f"[gewechat] Parse is_at from PushContent. self.is_at: {self.is_at}")

            # 如果是群消息，使用正则表达式去掉wxid前缀和@信息
            self.content = re.sub(f'{self.actual_user_id}:\n', '', self.content)  # 去掉wxid前缀
            self.content = re.sub(r'@[^\u2005]+\u2005', '', self.content)  # 去掉@信息
        else:
            # 如果不是群聊消息，保持结构统一，也要设置actual_user_id和actual_user_nickname
            self.actual_user_id = self.other_user_id
            self.actual_user_nickname = self.other_user_nickname

        self.my_msg = self.msg['Wxid'] == self.from_user_id  # 消息是否来自自己

    def download_voice(self):
        try:
            voice_data = self.client.download_voice(self.msg['Wxid'], self.msg_id)
            with open(self.content, "wb") as f:
                f.write(voice_data)
        except Exception as e:
            logger.error(f"[gewechat] Failed to download voice file: {e}")

    def download_image(self):
        try:
            # 尝试下载高清图片
            content_xml = self.msg['Data']['Content']['string']
            try:
                # Find the position of '<?xml' declaration and remove any prefix
                xml_start = content_xml.find('<?xml version=')
                if xml_start != -1:
                    content_xml = content_xml[xml_start:]
                image_info = self.client.download_image(app_id=self.app_id, xml=content_xml, type=1)
            except Exception as e:
                logger.warning(f"[gewechat] Failed to download high-quality image: {e}")
                # 尝试下载普通图片
                image_info = self.client.download_image(app_id=self.app_id, xml=content_xml, type=2)
            if image_info['ret'] == 200 and image_info['data']:
                file_url = image_info['data']['fileUrl']
                logger.info(f"[gewechat] Download image file from {file_url}")
                # 在需要时导入Config并创建实例
                from config import Config
                config = Config(file_path='./config.json', is_init=True)
                download_url = config.get("gewechat_download_url").rstrip('/')
                full_url = download_url + '/' + file_url
                try:
                    file_data = requests.get(full_url).content
                    with open(self.content, "wb") as f:
                        f.write(file_data)
                except Exception as e:
                    logger.error(f"[gewechat] Failed to download image file: {e}")
            else:
                logger.error(f"[gewechat] Failed to download image file: {image_info}")
        except Exception as e:
            logger.error(f"[gewechat] Failed to download image file: {e}")

    def prepare(self):
        if self._prepare_fn:
            self._prepare_fn()

    def _is_non_user_message(self, msg_source: str, from_user_id: str) -> bool:
        """检查消息是否来自非用户账号（如公众号、腾讯游戏、微信团队等）

        Args:
            msg_source: 消息的MsgSource字段内容
            from_user_id: 消息发送者的ID

        Returns:
            bool: 如果是非用户消息返回True，否则返回False

        Note:
            通过以下方式判断是否为非用户消息：
            1. 检查MsgSource中是否包含特定标签
            2. 检查发送者ID是否为特殊账号或以特定前缀开头
        """
        # 检查发送者ID
        special_accounts = ["Tencent-Games", "weixin"]
        if from_user_id in special_accounts or from_user_id.startswith("gh_"):
            logger.debug(f"[gewechat] non-user message detected by sender id: {from_user_id}")
            return True

        # 检查消息源中的标签
        # 示例:<msgsource>\n\t<tips>3</tips>\n\t<bizmsg>\n\t\t<bizmsgshowtype>0</bizmsgshowtype>\n\t\t<bizmsgfromuser><![CDATA[weixin]]></bizmsgfromuser>\n\t</bizmsg>
        non_user_indicators = [
            "<tips>3</tips>",
            "<bizmsgshowtype>",
            "</bizmsgshowtype>",
            "<bizmsgfromuser>",
            "</bizmsgfromuser>"
        ]
        if any(indicator in msg_source for indicator in non_user_indicators):
            logger.debug(f"[gewechat] non-user message detected by msg_source indicators")
            return True

        return False
