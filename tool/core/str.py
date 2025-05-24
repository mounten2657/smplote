import re
import time
import json
import random
import hashlib


class Str:
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
