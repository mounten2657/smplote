import xmltodict
from flask.globals import request
from tool.core import *
from utils.wechat.qywechat.callback.qy_verify_handler import QyVerifyHandler
from utils.wechat.qywechat.command.ai_command import AiCommand
from utils.wechat.qywechat.command.gpl_command import GplCommand
from utils.wechat.qywechat.command.smp_command import SmpCommand

logger = Logger()


@Ins.singleton
class QyCallbackHandler(Que):

    def msg_handler(self, app_key, params=None):
        """对外提供的开放方法"""
        logger.info(params, 'QY_MSG_CALL_PARAMS')
        if Http.get_request_method() == 'GET':
            # 初始化验证 - 一般只走一次
            return QyVerifyHandler.verify(app_key)
        xml = request.get_data()
        if len(xml) == 0:
            return 'invalid request'
        res = self.que_submit(app_key=app_key, xml=xml)
        return 'success' if res else 'error'

    def _que_exec(self, **kwargs):
        """队列执行方法入口"""
        app_key = kwargs.get('app_key')
        xml = kwargs.get('xml')
        return self._msg_handler(app_key, xml)

    @staticmethod
    def _msg_handler(app_key, xml):
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
        res = QyCallbackHandler._dispatch(data)
        return res

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
            commands = qy_config['command_list'].split(',')
            admins = qy_config['admin_list'].split(',')
            if msg_user in admins:
                # 仅管理员可用
                for k,v in enumerate(commands):
                    if content.lower().startswith(v):
                        method = f"exec_0_{k}"
                        break
        elif msg_type == 'event' and msg_event == 'click':
            # 菜单点击事件
            msg_key = data.get('EventKey', '').split('#')
            if len(msg_key) == 3 and msg_key[1]:
                msk = msg_key[1].split('_')
                method = f"exec{msg_key[1]}"
                if msk[1] == '0':  # AI 菜单
                    handler = AiCommand()
                elif msk[1] == '1':  # GPL 菜单
                    handler = GplCommand()
                elif msk[1] == '2':  # SMP 菜单
                    handler = SmpCommand()
                else:
                    pass  # 未识别的菜单放行
        else:
            pass  # 未识别的消息放行
        handler.set_content(content)
        action = getattr(handler, method)
        logger.debug([handler.__class__, method], 'QY_MSG_DIS_END')
        return action()

