import time
from xml.etree import ElementTree
from tool.db.cache.redis_task_queue import RedisTaskQueue
from utils.wechat.vpwechat.factory.vp_base_factory import VpBaseFactory
from utils.wechat.vpwechat.vp_client import VpClient
from tool.core import Logger, Attr

logger = Logger()


class VpCallbackHandler(VpBaseFactory):

    def on_message(self, data):
        """监听来自 ws 的回调消息 - 已过滤"""
        time.sleep(1)  # 避免太快了，处理不过来
        # 先入队列，再由队列发起回调处理
        # service.wechat.callback.vp_callback_service@VpCallbackService.callback_handler
        service = self.config['ws_service_path'] + '@VpCallbackService.callback_handler'
        return RedisTaskQueue().submit(service, data)

    def on_message_filter(self, data):
        """消息过滤器"""
        message = data['message']
        logger.debug(f"on message: {message}", 'VP_FLT')
        if not message:
            logger.error(f"on message: message body is not json string!", 'VP_FLT_ERR')
            return False
        # 过滤一些无用的信息
        app_config = self.app_config
        self_wxid = self.app_config['wxid']
        a_g_wxid = app_config['g_wxid']
        msg_id = message.get('new_msg_id', 0)
        msg_type = message.get('msg_type', 0)
        f_wxid = message.get('from_user_name', {}).get('str', '')
        t_wxid = message.get('to_user_name', {}).get('str', '')
        is_group = int('@chatroom' in f_wxid)
        is_my = int(f_wxid == self_wxid)
        is_sl = int(t_wxid == self_wxid and not is_group)
        if f_wxid:
            if msg_type == 51:  # 同步消息
                logger.warning(f"on message: 忽略消息[T1]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if 'gh_' in f_wxid:  # 公众号
                logger.warning(f"on message: 忽略消息[T2]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if f_wxid in str(app_config['g_wxid_exc']).split(','):  # 无用群
                logger.warning(f"on message: 忽略消息[T3]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if f_wxid not in str(a_g_wxid).split(',') and not (is_my or is_sl):  # 仅限特定群、自己发的消息 和 私聊
                logger.warning(f"on message: 忽略消息[T4]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
        data.update({
            "app_key": self.app_key,
            "self_wxid": self_wxid,
            "a_g_wxid": a_g_wxid,
            "is_group": is_group,
            "is_my": is_my,
            "is_sl": is_sl,
        })
        return data

    @staticmethod
    def rev_handler(params):
        """回调消息具体处理方法"""
        app_key = params['app_key']
        self_wxid = params['self_wxid']
        a_g_wxid = params['a_g_wxid']
        is_group = params['is_group']
        is_my = params['is_my']
        is_sl = params['is_sl']
        message = params['message']
        client = VpClient(app_key)
        msg_source = message.get('msg_source', '')
        push_content = message.get('push_content', '')
        contents = message.get('content', {}).get('str', '')
        f_wxid = message.get('from_user_name', {}).get('str', '')
        t_wxid = message.get('to_user_name', {}).get('str', '')
        if ':\n' in contents:
            send_wxid, content = str(contents).split(':\n', 1)
        elif is_my or is_sl:
            send_wxid, content = [f_wxid, str(contents).strip()]
        else:
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
            "a_g_wxid": a_g_wxid,
            "is_my": is_my,
            "is_sl": is_sl,
            "is_group": is_group,
        }
        # 判断是否at
        at_user = VpCallbackHandler.extract_at_user(msg_source)
        # is_at = 1 if self_wxid in str(at_user).split(',') else 0
        is_at = 1 if '在群聊中@了你' in push_content else 0
        msg.update({
            "at_user": at_user,
            "is_at": is_at,
        })
        g_wxid = msg['from_wxid'] if msg['is_group'] else ''
        # 补全昵称
        if g_wxid:
            room = client.get_room(g_wxid)
            send_user = Attr.select_item_by_where(room['member_list'], {'wxid': msg['send_wxid']})
            to_user = Attr.select_item_by_where(room['member_list'], {'wxid': msg['to_wxid']})
            msg['send_wxid_name'] = send_user.get('display_name', 'null')
            msg['to_wxid_name'] = to_user.get('display_name', 'null')
            msg['from_wxid_name'] = room.get('nickname', 'null')
        else:
            send_user = client.get_user(msg['send_wxid'])
            to_user = client.get_user(msg['to_wxid'])
            msg['send_wxid_name'] = send_user.get('remark_name') if len( send_user.get('remark_name')) else send_user.get('nickname', 'null')
            msg['to_wxid_name'] = to_user.get('remark_name') if len( to_user.get('remark_name')) else to_user.get('nickname', 'null')
            msg['from_wxid_name'] = msg['send_wxid_name']
        return True, msg

    @staticmethod
    def extract_at_user(msg_source):
        """提群被at的用户wxid"""
        try:
            root = ElementTree.fromstring(msg_source)
            at_user_node = root.find('atuserlist')
            return at_user_node.text if at_user_node is not None else ''
        except ElementTree.ParseError:
            return None
