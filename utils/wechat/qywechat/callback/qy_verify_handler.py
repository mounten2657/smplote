import base64, hashlib
from flask.globals import request
from Crypto.Cipher import AES
from tool.core import *

logger = Logger()


class QyVerifyHandler:
    """
    企业微信验证类
     - api doc - https://developer.work.weixin.qq.com/document/10514
     - debug = https://open.work.weixin.qq.com/wwopen/devtool/interface/combine
    """

    @staticmethod
    def check_base64_len(base64_str):
        """检查base64编码后数据位数是否正确"""
        len_remainder = 4 - (len(base64_str) % 4)
        if len_remainder == 0:
            return base64_str
        else:
            for temp in range(0, len_remainder):
                base64_str = base64_str + "="
            return base64_str

    @staticmethod
    def msg_base64_decrypt(ciphertext_base64, key_base64):
        """解密并提取消息正文"""
        # 处理密文、密钥和iv
        ciphertext_bytes = base64.b64decode(QyVerifyHandler.check_base64_len(ciphertext_base64))
        key_bytes = base64.b64decode(QyVerifyHandler.check_base64_len(key_base64))
        iv_bytes = key_bytes[:16]
        # 解密
        decr = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        plaintext_bytes = decr.decrypt(ciphertext_bytes)
        # 截取数据，判断消息正文字节数
        msg_len_bytes = plaintext_bytes[16:20]
        msg_len = int.from_bytes(msg_len_bytes, byteorder='big', signed=False)
        # 根据消息正文字节数截取消息正文，并转为字符串格式
        msg_bytes = plaintext_bytes[20:20 + msg_len]
        msg = str(msg_bytes, encoding='utf-8')
        return msg


    @staticmethod
    def check_msg_signature(msg_signature, token, timestamp, nonce, echostr):
        """消息体签名校验"""
        # 使用sort()从小到大排序[].sort()是在原地址改值的，所以如果使用li_s = li.sort()，li_s是空的，li的值变为排序后的值]
        li = [token, timestamp, nonce, echostr]
        li.sort()
        # 将排序结果拼接
        li_str = li[0] + li[1] + li[2] + li[3]
        # 计算SHA-1值
        sha1 = hashlib.sha1()
        # update()要指定加密字符串字符代码，不然要报错：
        # "Unicode-objects must be encoded before hashing"
        sha1.update(li_str.encode("utf8"))
        sha1_result = sha1.hexdigest()
        # 比较并返回比较结果
        if sha1_result == msg_signature:
            return True
        else:
            return False

    @staticmethod
    def verify(key):
        """
        企业微信初始化回调验证
        :param key:  APP 账号 - a1 | a2 | ...
        :return:  标准微信返回
        """
        app_config = Config.qy_config()['app_list'][key]
        token = app_config.get('verify_token')
        encoding_aes_key = app_config.get('verify_aes_key')
        msg_signature = request.args.to_dict().get("msg_signature")
        timestamp = request.args.to_dict().get("timestamp")
        nonce = request.args.to_dict().get("nonce")
        echo_str = request.args.get("echostr", "").replace(" ", "+")
        # 获取消息体签名校验结果
        check_result = QyVerifyHandler.check_msg_signature(msg_signature, token, timestamp, nonce, echo_str)
        if check_result:
            decrypt_result = QyVerifyHandler.msg_base64_decrypt(echo_str, encoding_aes_key)
            logger.info(decrypt_result, 'QY_VERIFY_SUCCESS')
            return decrypt_result
        else:
            logger.error(check_result, 'QY_VERIFY_FAILED')
            return ""

