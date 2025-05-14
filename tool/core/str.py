import re
import time
import random
import hashlib
import json


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
    def sub_str_len(s, max_len=65535, position=0,  encoding = 'utf-8'):
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
    def convert_to_json_dict(obj):
        """
        递归遍历对象，将里面的值对应的JSON字符串转换为字典/列表

        参数:
            obj: 任意类型的对象

        返回:
            处理后的对象，如果无法处理则返回原值
        """
        try:
            # 处理None
            if obj is None:
                return None
            # 处理字符串
            if isinstance(obj, str):
                # 尝试解析JSON
                try:
                    # 检查是否是JSON字符串（简单判断，避免解析普通字符串）
                    if (obj.startswith(('{', '[')) and obj.endswith(('}', ']'))):
                        return json.loads(obj)
                    return obj
                except (json.JSONDecodeError, TypeError):
                    return obj
            # 处理列表
            if isinstance(obj, list):
                return [Str.convert_to_json_dict(item) for item in obj]
            # 处理元组（转换为列表以保持可变性）
            if isinstance(obj, tuple):
                return tuple(Str.convert_to_json_dict(item) for item in obj)
            # 处理字典
            if isinstance(obj, dict):
                return {key: Str.convert_to_json_dict(value) for key, value in obj.items()}
            # 其他类型（数字、布尔值等）直接返回
            return obj
        except Exception:
            # 捕获所有异常，返回原值
            return obj

    @staticmethod
    def convert_to_json_string(obj):
        """
        将对象中的字典转换为JSON字符串

        参数:
            obj: 待处理的对象（字典、列表或其他类型）

        返回:
            处理后的对象
        """
        try:
            # 处理字典
            if isinstance(obj, dict):
                new_dict = {}
                for key, value in obj.items():
                    if isinstance(value, (dict, list, tuple)):
                        try:
                            new_dict[key] = json.dumps(value, ensure_ascii=False)
                        except (json.JSONDecodeError, TypeError):
                            new_dict[key] = value
                    else:
                        new_dict[key] = value
                return new_dict

            # 处理列表或元组
            if isinstance(obj, (list, tuple)):
                new_list = []
                for item in obj:
                    if isinstance(item, dict):
                        # 处理列表中的字典
                        new_item = {}
                        for key, value in item.items():
                            if isinstance(value, (dict, list, tuple)):
                                try:
                                    new_item[key] = json.dumps(value, ensure_ascii=False)
                                except (json.JSONDecodeError, TypeError):
                                    new_item[key] = value
                            else:
                                new_item[key] = value
                        new_list.append(new_item)
                    else:
                        new_list.append(item)
                return new_list if isinstance(obj, list) else tuple(new_list)

            # 其他类型直接返回
            return obj

        except Exception:
            return obj



