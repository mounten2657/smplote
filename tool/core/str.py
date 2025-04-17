import time
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






