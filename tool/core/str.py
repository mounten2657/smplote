import re
import time
import json
import html
import random
import base64
import hashlib
import urllib.parse
from urllib.parse import unquote, quote
from decimal import Decimal, ROUND_HALF_UP
from pypinyin import pinyin, Style
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
    def filter_target_chars(input_str: str) -> str:
        """
        过滤字符串，仅保留指定字符：
         - 数字（0-9）、英文（a-z/A-Z）、中文汉字（\u4e00-\u9fa5）、
         - 书名号（《》）、英文下划线（_）、中划线（-）、小数点（.）

        :param input_str: 待过滤的原始字符串
        :return: 过滤后的字符串（空字符串输入时返回空）
        """
        # 正则匹配规则：
        # [0-9]：数字；[a-zA-Z]：英文；[\u4e00-\u9fa5]：中文汉字
        # 《》：书名号；_：下划线；-：中划线；.：小数点
        pattern = r'[^\u4e00-\u9fa5a-zA-Z0-9《》_\-.]'
        # 替换非目标字符为空字符串
        return re.sub(pattern, '', input_str)

    @staticmethod
    def int(str_val, default=0):
        # 将字符串转换成整数，不成功就是 0
        try:
            return int(str_val)
        except Exception:
            return default

    @staticmethod
    def is_int(str_val):
        # 判断是否为整数
        try:
            int(str_val)
            return True
        except Exception:
            return False

    @staticmethod
    def float(str_val, default=0.0):
        # 将字符串转换成浮点数，不成功就是 0.0
        try:
            return float(str_val)
        except Exception:
            return default

    @staticmethod
    def is_float(str_val):
        # 判断是否为浮点数
        try:
            float(str_val)
            return True
        except Exception:
            return False

    @staticmethod
    def round(str_val, p=2):
        """四舍五入保留两位小数 - 返回 Decimal 类型"""
        return Decimal(str(str_val)).quantize(Decimal(f"0.{'0' * p}" if p >0 else '0'), rounding=ROUND_HALF_UP)

    @staticmethod
    def randint(start=1, end=100):
        """返回随机整数"""
        return random.randint(int(start), int(end))

    @staticmethod
    def rev_float(f, n=3, p=0, d='.'):
        """返回补0后的逆转字符串"""
        float_str = str(f)
        if '.' in float_str:
            integer_part, decimal_part = float_str.split('.', 1)
        else:
            integer_part = float_str
            decimal_part = ''
        padded_decimal = decimal_part.ljust(n, '0')
        reversed_decimal = padded_decimal[::-1]
        padded_integer = integer_part.rjust(p, '0')
        reversed_integer = padded_integer[::-1]
        return f"{reversed_decimal}{d}{reversed_integer}"

    @staticmethod
    def base64_encode(data: str, encoding: str = 'utf-8') -> str:
        """
        将字符串进行Base64编码

        :param str data: 待编码的字符串
        :param str encoding: 字符串编码格式，默认为'utf-8'
        :return: 编码后的Base64字符串
        """
        try:
            data_bytes = data.encode(encoding)
            encoded_bytes = base64.b64encode(data_bytes)
            encoded_str = encoded_bytes.decode(encoding)
            return encoded_str
        except Exception as e:
            return ''

    @staticmethod
    def base64_decode(encoded_data: str, encoding: str = 'utf-8') -> str:
        """
        对Base64编码的字符串进行解码

        :param str encoded_data: 待解码的Base64字符串
        :param str encoding: 解码后的字符串编码格式，默认为'utf-8'
        :return: 解码后的原始字符串
        :raises ValueError: 当输入数据不是有效的Base64字符串时抛出
        """
        try:
            encoded_bytes = encoded_data.encode(encoding)
            decoded_bytes = base64.b64decode(encoded_bytes)
            decoded_str = decoded_bytes.decode(encoding)
            return decoded_str
        except Exception as e:
            return ''

    @staticmethod
    def parse_json_string_ignore(value):
        """尝试将值序列化为JSON"""
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            # 无法序列化为JSON，使用原始值
            serialized_value = value
        return serialized_value

    @staticmethod
    def url_encode(url):
        """url编码"""
        return quote(url)

    @staticmethod
    def url_decode(url):
        """url解码"""
        return unquote(url)

    @staticmethod
    def first_py_char(text):
        """获取中文的首字母"""
        return ''.join(pinyin(text, style=Style.FIRST_LETTER, strict=False)[i][0] for i in range(len(text)))

    @staticmethod
    def replace_multiple(text, old_values, new_values=None):
        """
        一次性替换字符串中的多个子串

        :param text: 原始字符串
        :param old_values: 需要替换的子串列表
        :param new_values: 对应的替换值列表，默认空字符串列表
        :return:  替换后的字符串
        """
        # 处理默认值：如果 new_values 未提供，全部替换为空字符串
        if new_values is None:
            new_values = [''] * len(old_values)
        # 检查参数长度匹配
        if len(old_values) != len(new_values):
            raise ValueError("old_values 和 new_values 的长度必须相同")
        # 创建替换字典
        replacements = dict(zip(old_values, new_values))
        # 构建正则表达式模式
        pattern = re.compile('|'.join(re.escape(key) for key in replacements.keys()))
        # 执行替换
        return pattern.sub(lambda x: replacements[x.group()], text)

    @staticmethod
    def remove_mult_lines(text, deep=3):
        """删除多余的空行"""
        text = text.replace('\r', '\n')
        r1, r2 = ([("\n" * (i + 2)) for i in range(deep - 1)][::-1], ["\r\n"] * (deep - 1))
        return Str.replace_multiple(text, r1, r2)

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
        if not isinstance(s, str):
            return ""
        if not s or len(s) <= max_len:
            return s
        # 检测实际编码（比直接使用utf-8更安全）
        # encoding = chardet.detect(s.encode())['encoding'] or 'utf-8'
        try:
            if position == 0:
                while max_len > 0:
                    try:
                        return s[:max_len].encode(encoding)[:max_len].decode(encoding)
                    except UnicodeDecodeError:
                        max_len -= 1
            elif position == 1:
                while max_len > 0:
                    try:
                        return s[-max_len:].encode(encoding)[-max_len:].decode(encoding)
                    except UnicodeDecodeError:
                        max_len -= 1
            return s[:0]  # 理论上不会执行到这里
        except Exception:
            return s[:max_len] if position == 0 else s[-max_len:]

    @staticmethod
    def extract_ip(text):
        """从文本中提取IP地址 - ipv4"""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        return re.findall(ip_pattern, text)

    @staticmethod
    def remove_html_tags(s):
        """去除字符串中的标签"""
        try:
            return re.sub(r'<[^>]*>', '', s)
        except:
            return s

    @staticmethod
    def html_unescape(s, max_iter=9):
        """字符串实体转义"""
        try:
            for _ in range(max_iter):
                new_s = html.unescape(s)
                if new_s == s:
                    break
                s = new_s
            return s
        except:
            return ''
