import xml.etree.ElementTree as ET
from utils.wechat.gewechat.ge_client import GeClient
from tool.core import *

logger = Logger()


class GeMsgFormatter():
    """gewechat 回调消息格式化"""

    def parse_msg(self, msg):
        """格式化消息"""
        ret = {'create_time': msg.get('Data', {}).get('CreateTime', 0)}
        if not msg.get('Data'):
            err_msg = f"[gewechat] Missing 'Data' in message"
            logger.error(err_msg)
            raise RuntimeError(err_msg)
        if 'NewMsgId' not in msg['Data']:
            err_msg = f"[gewechat] Missing 'NewMsgId' in message data"
            logger.error(err_msg)
            raise RuntimeError(err_msg)
        # 消息ID
        ret['msg_id'] = msg['Data']['NewMsgId']
        # 消息类型
        ret['ctype'] = msg['Data']['MsgType']
        # 是否为自己的消息
        ret['my_msg'] = msg['Wxid'] == msg['Data']['FromUserName']['string']
        # 是否艾特自己
        ret['is_at'] = self.is_at_self(msg)
        # 是否群聊消息
        ret['is_group'] = True if "@chatroom" in msg['Data']['FromUserName']['string'] else False
        # 接收方
        ret['other_user_id'] = msg['Data']['FromUserName']['string']
        ret['other_user_nickname'] = self.get_frd_name(ret['other_user_id'])
        # 发送方
        ret['actual_user_id'] = msg['Data']['ToUserName']['string']
        ret['actual_user_nickname'] = self.get_frd_name(ret['actual_user_id'])
        # 消息内容
        ret['content'] = msg['Data']['Content']['string']
        # 转为对象返回
        return Attr.dict_to_obj(ret)

    def is_at_self(self, msg):
        """检查是否为艾特自己"""
        is_at = False
        msg_source = msg.get('Data', {}).get('MsgSource', '')
        if msg_source:
            try:
                root = ET.fromstring(msg_source)
                at_elem = root.find('atuserlist')
                if at_elem is not None:
                    at_list = at_elem.text
                    is_at = msg['Data']['ToUserName']['string'] in at_list
            except ET.ParseError:
                pass
        return is_at

    def get_frd_name(self, wxid):
        """获取好友昵称"""
        brief_info = GeClient().get_friend_detail_info(wxid)
        return brief_info.get('nickName', brief_info.get('alias', brief_info.get('userName', '')))


