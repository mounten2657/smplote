import re
import time
import json
import html
import random
import hashlib
import urllib.parse
from tool.core.env import Env


class Str:

    # 特殊字符码表
    SPECIAL_MAP = {
        # 控制字符 (Z0-Z9)
        '\x00': 'Z0',  # 空字符
        '\x01': 'Z1',  # 标题开始
        '\x02': 'Z2',  # 正文开始
        '\x03': 'Z3',  # 正文结束
        '\x04': 'Z4',  # 传输结束
        '\x05': 'Z5',  # 查询
        '\x06': 'Z6',  # 确认
        '\x07': 'Z7',  # 响铃
        '\x08': 'Z8',  # 退格
        '\x0b': 'Z9',  # 垂直制表符
        # 常用ASCII特殊符号 (Za-Zz)
        '/': 'Za', '.': 'Zb', '!': 'Zc', '@': 'Zd',
        '#': 'Ze', '$': 'Zf', '%': 'Zg', '^': 'Zh',
        '&': 'Zi', '*': 'Zj', '(': 'Zk', ')': 'Zl',
        '-': 'Zm', '_': 'Zn', '=': 'Zo', '+': 'Zp',
        '|': 'Zq', '?': 'Zr', ',': 'Zs', '~': 'Zt',
        '`': 'Zu', '"': 'Zv', "'": 'Zw', '\\': 'Zx',
        ':': 'Zy', ';': 'Zz',
        # 扩展Unicode (ZA-ZY)
        '[': 'ZA', ']': 'ZB', '{': 'ZC', '}': 'ZD',
        '<': 'ZE', '>': 'ZF', ' ': 'ZG', '\t': 'ZH',
        '\n': 'ZI', '\r': 'ZJ', '\x0c': 'ZK', '£': 'ZL',
        '¥': 'ZM', '©': 'ZN', '®': 'ZO', '°': 'ZP',
        '±': 'ZQ', 'µ': 'ZR', '¶': 'ZS', '·': 'ZT',
        '¿': 'ZU', 'À': 'ZV', 'Á': 'ZW', 'Â': 'ZX',
        'Ã': 'ZY',
        # 明文字符Z必须放在最后（优先级最低）
        'Z': 'ZZ'
    }
    REVERSE_SPECIAL = {v: k for k, v in SPECIAL_MAP.items()}

    @staticmethod
    def encrypt_str(content: str, key: str = '') -> str:
        """加密字符串"""
        key = key if key else Env.get('APP_CONFIG_MASTER_KEY')
        content = urllib.parse.quote(content)  # 中文转码
        # 生成密钥流
        hmac = hashlib.pbkdf2_hmac('sha256', key.encode(), b'salt', 100000)
        key_stream = hmac.hex()
        # 前3字符转6位16进制
        prefix = (content[:3].encode().hex() if len(content) >= 3
                  else content.encode().hex().ljust(6, '0'))
        # 加密后续字符
        encrypted = []
        for i, c in enumerate(content[3:]):
            # 优先处理Z和其他特殊符号
            if c in Str.SPECIAL_MAP:
                encrypted.append(Str.SPECIAL_MAP[c])
                continue
            # 处理常规字符（加密结果限制在0-9a-zA-Y）
            key_char = key_stream[(i + 6) % len(key_stream)]
            shift = ord(key_char) % 61  # 61 = 10数字 + 26小写 + 25大写（排除Z）
            code = Str._shift_code(c)
            # 加密计算（结果范围0-60）
            encrypted_code = (code + shift) % 61
            # 映射到输出字符
            if encrypted_code < 10:
                encrypted.append(str(encrypted_code))
            elif encrypted_code < 36:
                encrypted.append(chr(ord('a') + encrypted_code - 10))
            else:
                encrypted.append(chr(ord('A') + encrypted_code - 36))
        return prefix + ''.join(encrypted)

    @staticmethod
    def decrypt_str(encrypted: str, key: str = '') -> str:
        """解密字符串"""
        key = key if key else Env.get('APP_CONFIG_MASTER_KEY')
        hmac = hashlib.pbkdf2_hmac('sha256', key.encode(), b'salt', 100000)
        key_stream = hmac.hex()
        # 解析前6位16进制
        prefix = bytes.fromhex(encrypted[:6]).decode(errors='replace')[:3]
        # 解密后续字符
        decrypted = []
        i = 0
        while i < len(encrypted[6:]):
            # 检查是否为特殊符号（Z后跟数字/字母）
            if i + 1 < len(encrypted[6:]) and encrypted[6 + i] == 'Z':
                special_code = encrypted[6 + i:8 + i]
                if special_code in Str.REVERSE_SPECIAL:
                    decrypted.append(Str.REVERSE_SPECIAL[special_code])
                    i += 2
                    continue
            # 处理常规字符
            c = encrypted[6 + i]
            key_char = key_stream[(len(decrypted) + 6) % len(key_stream)]
            shift = ord(key_char) % 61
            code = Str._shift_code(c)
            # 解密计算
            orig_code = (code - shift) % 61
            # 还原字符
            if orig_code < 10:
                decrypted.append(str(orig_code))
            elif orig_code < 36:
                decrypted.append(chr(ord('a') + orig_code - 10))
            else:
                decrypted.append(chr(ord('A') + orig_code - 36))
            i += 1
        dec = prefix + ''.join(decrypted)
        return urllib.parse.unquote(dec)

    @staticmethod
    def _shift_code(c):
        """获取特殊字符码"""
        if c.isdigit():
            code = int(c)
        elif c.islower():
            code = 10 + ord(c) - ord('a')
        elif c.isupper() and c != 'Z':
            code = 36 + ord(c) - ord('A')
        else:
            code = 0
        return code

    @staticmethod
    def uuid():
        # 获取当前时间戳（精确到毫秒）
        timestamp = int(time.time() * 1000)
        # 生成随机数
        random_part1 = random.randint(0, 0xFFFF)
        random_part2 = random.randint(0, 0xFFFF)
        random_part3 = random.randint(0, 0xFFFFFFFFFFFF)

        # 时间戳转换为十六进制
        timestamp_hex = format(timestamp, '016x')
        # 随机数转换为十六进制
        random_part1_hex = format(random_part1, '04x')
        random_part2_hex = format(random_part2, '04x')
        random_part3_hex = format(random_part3, '012x')

        # 组合成 UUID 格式
        # 这里的 1 表示版本 1（基于时间）
        unique_id = f"{timestamp_hex[:8]}-{timestamp_hex[8:12]}-1{timestamp_hex[12:15]}-{random_part1_hex}-{random_part2_hex}{random_part3_hex}"
        return Str.md5(unique_id)

    @staticmethod
    def md5(data):
        # 创建 MD5 对象
        md5 = hashlib.md5()
        # 更新 MD5 对象的内容，需要将字符串编码为字节类型
        md5.update(data.encode('utf-8'))
        # 获取十六进制表示的哈希值
        return md5.hexdigest()

    @staticmethod
    def int(str_val):
        # 将字符串转换成整数，不成功就是0
        try:
            return int(str_val) if (str_val and str(str_val).strip()) else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def parse_json_string_ignore(value):
        # 尝试将值序列化为JSON
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            # 无法序列化为JSON，使用原始值
            serialized_value = value
        return serialized_value

    @staticmethod
    def sub_str_len(s, max_len=65535, position=0, encoding='utf-8'):
        """
        安全截取包含中文的字符串（防止乱码）
        :param s: 输入内容（非字符串类型将返回空字符串）
        :param max_len: 最大长度（默认65535）
        :param position: 截取位置（0=从头截取，1=从尾部截取）
        :param encoding: 字符串编码，默认utf-8
        :return: 截取后的字符串
        """
        # 非字符串类型检查
        if not isinstance(s, str):
            return ""

        # 空字符串或无需截取的情况
        if not s or len(s) <= max_len:
            return s

        # 检测实际编码（比直接使用utf-8更安全）
        # encoding = chardet.detect(s.encode())['encoding'] or 'utf-8'

        try:
            # 从头部截取
            if position == 0:
                while max_len > 0:
                    try:
                        return s[:max_len].encode(encoding)[:max_len].decode(encoding)
                    except UnicodeDecodeError:
                        max_len -= 1

            # 从尾部截取
            elif position == 1:
                while max_len > 0:
                    try:
                        return s[-max_len:].encode(encoding)[-max_len:].decode(encoding)
                    except UnicodeDecodeError:
                        max_len -= 1

            return s[:0]  # 理论上不会执行到这里

        except Exception:
            # 极端情况保底处理
            return s[:max_len] if position == 0 else s[-max_len:]

    @staticmethod
    def extract_ip(text):
        """
        从文本中提取IP地址

        参数:
        text (str): 包含IP地址的文本

        返回:
        list: 提取到的IP地址列表，如果没有则返回空列表
        """
        # 匹配IPv4地址的正则表达式
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        return re.findall(ip_pattern, text)

    @staticmethod
    def html_unescape(s):
        """字符串实体转义"""
        try:
            return html.unescape(s)
        except:
            return ''

    @staticmethod
    def remove_html_tags(s):
        """去除字符串中的标签"""
        try:
            return re.sub(r'<[^>]*>', '', s)
        except:
            return s

    @staticmethod
    def extract_attr(contents, key_name, position=1):
        """
        从普通文本中提取特定的属性
          - \\s*=\\s*：匹配等号=，允许等号前后有任意数量的空白字符（如空格、制表符）。
          - ["\']：匹配单引号或双引号。
          - ([^"\']+)：捕获组，匹配除单引号和双引号之外的任意字符（至少一个）。
          - ["\']：再次匹配单引号或双引号，与前面的引号类型对应。

        :param contents:  普通文本 - 'xxx k1="v1" xxx k2=\'v2\' xxx'
        :param key_name:  匹配的标签名
        :param position:  匹配第几个标签
        :return: 匹配结果
        """
        """"""
        pattern = re.compile(fr'{key_name}\s*=\s*["\']([^"\']+)["\']')
        matches = pattern.finditer(contents)
        results = [match.group(1) for match in matches]
        if 1 <= position <= len(results):
            return results[position - 1]
        return ''

    @staticmethod
    def extract_xml_attr(contents, key_name, position=1):
        """
        从xml文本中提取特定的属性
          - 使用非贪婪匹配 ([^<]+?) 确保只匹配到下一个闭合标签
          - 添加 CDATA 处理：(?:<!\\[CDATA\\[)?` 和 `(?:\\]\\]>)? 分别匹配 CDATA 的开始和结束标记
          - 使用 (.*?) 非贪婪匹配捕获标签内的所有内容，包括嵌套标签和 CDATA 标记
          - 使用 \\s* 处理标签内可能的空白字符

        :param contents:  xml 文本 - "xxx<k1>v1</k1> xxx <k2><![CDATA[v2]]></k2> xxx"
        :param key_name:  匹配的标签名
        :param position:  匹配第几个标签
        :return: 匹配结果
        """
        """"""
        pattern = re.compile(
            fr'<{key_name}>\s*(?:<!\[CDATA\[)?(.*?)(?:]]>)?\s*</{key_name}>',
            re.DOTALL  # 使 . 匹配包括换行符在内的所有字符
        )
        matches = pattern.finditer(contents)
        results = [match.group(1) for match in matches]
        if 1 <= position <= len(results):
            return results[position - 1]
        return ''
