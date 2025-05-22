from xml.etree import ElementTree
from utils.wechat.vpwechat.factory.vp_base_factory import VpBaseFactory
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Logger, Attr

logger = Logger


class VpMsgFormatter(VpBaseFactory):

    def context(self, params):
        """消息格式化"""
        app_key = params['app_key']
        self_wxid = params['self_wxid']
        g_wxid = params['g_wxid']
        is_my = params['is_my']
        is_sl = params['is_sl']
        client = VpClient(app_key)
        # 微信回调的源信息
        message = params['message']
        msg_source = message.get('msg_source', '')
        push_content = message.get('push_content', '')
        contents = message.get('content', {}).get('str', '')
        f_wxid = message.get('from_user_name', {}).get('str', '')
        t_wxid = message.get('to_user_name', {}).get('str', '')
        # 消息分类处理
        if 'emoji_biaoqing_todo' in contents:  # 表情 - "{s_wxid}:\n{<emoji_xml>}"
            send_wxid, content = [f_wxid, str(contents).strip()]
        elif 'pattedusername' in contents:  # 拍一拍 - "{g_wxid}:\n{<pat_xml>}" | "{<pat_xml>}"
            pat = self.extract_pat_info(contents, t_wxid, client)
            if pat:
                f_wxid, t_wxid, g_wxid, content = pat
                send_wxid = f_wxid
            else:
                send_wxid, content = [f_wxid, str(contents).strip()]
        elif is_my or is_sl:  # 自己的消息 或 私聊消息 - "{content}"
            send_wxid, content = [f_wxid, str(contents).strip()]
        elif ':\n' in contents: # 普通消息 - "{s_wxid}:\n{content}"
            send_wxid, content = str(contents).split(':\n', 1)
        else:  # 未识别 - 不放行
            send_wxid, content = ['', '']
        msg = {
            "msg_id": message.get('new_msg_id', 0),
            "msg_type": message.get('msg_type', 0),
            "from_wxid": f_wxid,
            "from_wxid_name": '',
            "to_wxid": t_wxid,
            "to_wxid_name": '',
            "send_wxid": send_wxid if send_wxid else f_wxid,
            "send_wxid_name": '',
            "content": content,
            "app_key": app_key,
            "self_wxid": self_wxid,
            "is_my": is_my,
            "is_sl": is_sl,
            "is_group": 1 if g_wxid else 0,
            "g_wxid": g_wxid,
        }
        # 判断是否at
        at_user = self.extract_at_user(msg_source)
        # is_at = 1 if self_wxid in str(at_user).split(',') else 0
        is_at = 1 if '在群聊中@了你' in push_content else 0
        msg.update({
            "at_user": at_user,
            "is_at": is_at,
        })
        # 补全昵称
        if g_wxid:  # 群聊 - 优先群备注名
            room = client.get_room(g_wxid)
            send_user = Attr.select_item_by_where(room['member_list'], {'wxid': msg['send_wxid']})
            to_user = Attr.select_item_by_where(room['member_list'], {'wxid': msg['to_wxid']})
            msg['send_wxid_name'] = send_user.get('display_name', 'null') if send_user else 'null'
            msg['to_wxid_name'] = to_user.get('display_name', 'null') if to_user else 'null'
            msg['from_wxid_name'] = room.get('nickname', 'null')
        else:  # 私聊 - 优先备注名
            send_user = client.get_user(msg['send_wxid'])
            to_user = client.get_user(msg['to_wxid'])
            msg['send_wxid_name'] = send_user.get('remark_name') if len( send_user.get('remark_name')) else send_user.get('nickname', 'null')
            msg['to_wxid_name'] = to_user.get('remark_name') if len( to_user.get('remark_name')) else to_user.get('nickname', 'null')
            msg['from_wxid_name'] = msg['send_wxid_name']
        return msg

    @staticmethod
    def extract_at_user(msg_source):
        """提群被at的用户wxid"""
        try:
            root = ElementTree.fromstring(msg_source)
            at_user_node = root.find('atuserlist')
            return at_user_node.text if at_user_node is not None else ''
        except ElementTree.ParseError:
            return None

    @staticmethod
    def extract_pat_info(contents, t_wxid, client):
        """解析拍一拍信息"""
        try:
            if ':\n' in contents:  # 别人拍我 - "{g_wxid}:\n{<content_xml>}"
                g_wxid, content_xml = str(contents).split(':\n', 1)
            else:  # 我拍别人 - "{<content_xml>}"
                g_wxid, content_xml = [t_wxid, contents]
            # 从 xml 匹配节点
            root = ElementTree.fromstring(content_xml)
            pat_node = root.find('.//pat')
            f_wxid = pat_node.findtext('fromusername')
            t_wxid = pat_node.findtext('pattedusername')
            pat_suffix = pat_node.findtext('patsuffix')
            # 获取成员信息
            room = client.get_room(g_wxid)
            f_user = Attr.select_item_by_where(room['member_list'], {'wxid': f_wxid})
            t_user = Attr.select_item_by_where(room['member_list'], {'wxid': t_wxid})
            f_user_name = f_user.get('display_name', f_wxid) if f_user else f_wxid
            t_user_name = t_user.get('display_name', t_wxid)  if t_user else t_user
            content = f"[拍一拍消息] {f_user_name} 拍了拍 {t_user_name} {pat_suffix}"
            # import re
            # pat_template = pat_node.findtext('template')
            # wxid_name = {"wxid_xxx": "张三"}
            # content = re.sub(r'"?\${(.*?)}"?', lambda m: wxid_name.get(m.group(1), m.group()), pat_template)
            return f_wxid, t_wxid, g_wxid, content
        except ElementTree.ParseError:
            return None




