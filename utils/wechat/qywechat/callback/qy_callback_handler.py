import xmltodict
from tool.core import Logger, Str, Config, Time
from tool.db.cache.redis_client import RedisClient
from utils.wechat.qywechat.callback.qy_verify_handler import QyVerifyHandler
from utils.wechat.qywechat.command.ai_command import AiCommand
from utils.wechat.qywechat.command.gpl_command import GplCommand
from utils.wechat.qywechat.command.smp_command import SmpCommand

logger = Logger()


class QyCallbackHandler:

    @staticmethod
    def msg_handler(app_key, xml):
        """
        企业微信消息回调处理
        :param app_key:  APP 账号 - a1 | a2 | ...
        :return:  标准微信返回
        """
        app_config = Config.qy_config()['app_list'][app_key]
        encoding_aes_key = app_config.get('verify_aes_key')
        logger.debug(xml, 'QY_MSG_CALL_XML')
        xml_data = xmltodict.parse(xml)
        logger.info(xml_data, 'QY_MSG_CALL_XML_DATA')
        # 解密XML
        decrypt_result = QyVerifyHandler.msg_base64_decrypt(xml_data['xml']['Encrypt'], encoding_aes_key)
        decrypt_result = xmltodict.parse(decrypt_result)
        logger.info(decrypt_result, 'QY_MSG_CALL_DES')
        # 点击事件 # {'xml': {'ToUserName': 'ww36b39b33bbf1b2f0', 'FromUserName': 'WuJun', 'CreateTime': '1747014396', 'MsgType': 'event', 'AgentID': '1000002', 'Event': 'click', 'EventKey': '#sendmsg#_2_0#7599826077209668'}}
        # 文本消息 # {'xml': {'ToUserName': 'ww36b39b33bbf1b2f0', 'FromUserName': 'WuJun', 'CreateTime': '1747017605', 'MsgType': 'text', 'Content': '123456789', 'MsgId': '7503383482518056014', 'AgentID': '1000002'}}
        data = decrypt_result.get('xml', {})
        # 加锁去重
        Time.sleep(Str.randint(1, 20) / 10)
        md5 = Str.md5(str(data))
        if not RedisClient().set_nx('LOCK_QY_CAL', 1, [md5]):
            return False, data
        res = QyCallbackHandler._dispatch(data)
        return res, data

    @staticmethod
    def _dispatch(data):
        """回调任务自动分配"""
        msg_type = data.get('MsgType')
        msg_event = data.get('Event')
        msg_user = data.get('FromUserName')
        content = data.get('Content')
        qy_config = Config.qy_config()
        handler = AiCommand()
        method = 'exec_null'
        logger.debug([msg_type, msg_event, msg_user, content], 'QY_MSG_DIS_STA')
        if msg_type == 'text':
            # 用户回复消息
            # commands = qy_config['command_list'].split(',')
            commands_map = {
                "#提问": "qy_que",
                "#百科": "qy_sci",
            }
            admins = qy_config['admin_list'].split(',')
            if msg_user in admins:
                for k, v in commands_map.items():
                    if content.lower().startswith(k):
                        method = v
                        break
        elif msg_type == 'event' and msg_event == 'click':
            # 菜单点击事件
            # {'Event': 'click', 'EventKey': '#sendmsg#_2_4#7599827414208614'}
            msg_key = data.get('EventKey', '').split('#')
            if len(msg_key) == 4 and msg_key[2]:
                method = f"exec{msg_key[2]}"
                m_type = msg_key[2].split('_')[1]
                if m_type == '0':  # AI 菜单
                    handler = AiCommand()
                elif m_type == '1':  # GPL 菜单
                    handler = GplCommand()
                elif m_type == '2':  # SMP 菜单
                    handler = SmpCommand()
                else:
                    pass  # 未识别的菜单放行
        else:
            pass  # 未识别的消息放行
        handler.set_content(content)
        handler.set_user({"id": msg_user, "name": msg_user})
        action = getattr(handler, method)
        logger.debug([handler.__class__, method], 'QY_MSG_DIS_END')
        return action()

