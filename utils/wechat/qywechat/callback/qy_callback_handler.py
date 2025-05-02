import xmltodict
from flask.globals import request
from qy_verify_handler import QyVerifyHandler
from tool.core import *

logger = Logger()


@Ins.singleton
class QyCallbackHandler(Que):

    def msg_handler(self, app_key):
        """对外提供的开放方法"""
        xml = request.get_data()
        return self.que_submit(app_key=app_key, xml=xml)

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
        # do something ...
        return "success"
