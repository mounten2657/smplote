from tool.db.cache.redis_task_queue import RedisTaskQueue
from utils.wechat.vpwechat.factory.vp_base_factory import VpBaseFactory
from utils.wechat.vpwechat.formatter.vp_msg_formatter import VpMsgFormatter
from tool.core import Logger, Error, Str, Time

logger = Logger()


class VpCallbackHandler(VpBaseFactory):

    def on_message(self, data):
        """监听来自 ws 的回调消息"""
        data = self.on_message_filter(data)  # 消息过滤
        if not data:
            return False
        Time.sleep(0.01)  # 避免满载
        # 先入队列，再由队列发起回调处理 - 队列分流，开4个队列一起消费
        res = RedisTaskQueue(f'rtq_vp_ch{Str.randint(1, 4)}_queue').add_task('VP_CH', data)
        return res

    def on_message_filter(self, data):
        """消息过滤器 - 简单处理，不涉及数据查询，主要用于过滤一些不需要的消息"""
        message = data['message']
        logger.debug(f"on message: {message}", 'VP_FLT')
        if not message:
            logger.error(f"on message: message body is not json string!", 'VP_FLT_ERR')
            return False
        # 过滤一些无用的信息
        app_config = self.app_config
        self_wxid = self.self_wxid
        a_g_wxid = self.a_g_wxid
        msg_id = message.get('new_msg_id', 0)
        p_msg_id = message.get('msg_id', 0)
        msg_id = f"{p_msg_id}-{msg_id}"  # 展示用
        msg_type = message.get('msg_type', 0)
        msg_source = message.get('msg_source', '')
        contents = message.get('content', {}).get('str', '')
        f_wxid = message.get('from_user_name', {}).get('str', '')
        t_wxid = message.get('to_user_name', {}).get('str', '')
        g_wxid = f_wxid if '@chatroom' in f_wxid else (t_wxid if '@chatroom' in t_wxid else '')
        is_my = int(f_wxid == self_wxid)
        is_sl = int(not g_wxid)
        if f_wxid:
            if 'a2' == self.app_key and f_wxid != self.config['app_list']['a1']['wxid']:  # 小号只接收来自主账号的消息
                logger.warning(f"on message: 忽略消息[T0]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            # 临时测试 - 只接收指定群
            # if 'a1' == self.app_key and (g_wxid != self.config['app_list']['a2']['g_wxid'] and t_wxid != self.config['app_list']['a2']['g_wxid']):
            #     logger.warning(f"on message: 忽略消息[T0]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
            #     return False
            if 51 == msg_type:  # 同步消息
                logger.warning(f"on message: 忽略消息[T1]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if 'weixin' == f_wxid:  # 微信团队
                logger.warning(f"on message: 忽略消息[T11]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if 'gh_' in f_wxid:  # 公众号
                logger.warning(f"on message: 忽略消息[T2]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if all(key in msg_source for key in ('bizmsg', 'bizclientmsgid')):  # 隐蔽公众号
                logger.warning(f"on message: 忽略消息[T21]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if all(key in contents for key in ('announcement', 'sourceid', 'htmlid')):  # 群公告
                logger.warning(f"on message: 忽略消息[T22]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if f_wxid in str(app_config['g_wxid_exc']).split(','):  # 无用群
                logger.warning(f"on message: 忽略消息[T3]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            if '@openim' in f_wxid:  # 无用企业号
                logger.warning(f"on message: 忽略消息[T31]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
                return False
            # if f_wxid not in str(a_g_wxid).split(',') and not (is_my or is_sl):  # 仅限特定群、自己发的消息 和 私聊
            #     logger.warning(f"on message: 忽略消息[T4]<{msg_id}> 来自 <{f_wxid}>", 'VP_FLT_SKP')
            #     return False
        data.update({
            "app_key": self.app_key,
            "self_wxid": self_wxid,
            "g_wxid": g_wxid,
            "is_my": is_my,
            "is_sl": is_sl,
        })
        return data

    @staticmethod
    def rev_handler(params):
        """回调消息具体处理方法"""
        try:
            # 交由消息格式器处理
            app_key = params['app_key']
            msg = VpMsgFormatter(app_key).context(params)
            if not isinstance(msg, dict):
                return False, {"err_msg": f"解析消息失败", "err_data": msg}
            return True, msg
        except Exception as e:
            return False, Error.handle_exception_info(e)
