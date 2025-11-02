import re
import time
import json
import html
import random
import base64
import hashlib
import urllib.parse
from pypinyin import pinyin, Style
from urllib.parse import unquote, quote
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
    def int(str_val, default=None):
        # 将字符串转换成整数，不成功就是 None
        try:
            return int(str_val)
        except Exception:
            return default

    @staticmethod
    def float(str_val, default=None):
        # 将字符串转换成浮点数，不成功就是 None
        try:
            return float(str_val)
        except Exception:
            return default

    @staticmethod
    def randint(start=1, end=100):
        """返回随机整数"""
        return random.randint(int(start), int(end))

    @staticmethod
    def rev_float(f, n=3, p=0):
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
        return f"{reversed_decimal}.{reversed_integer}"

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

        参数:
        text (str): 原始字符串
        old_values (list): 需要替换的子串列表
        new_values (list): 对应的替换值列表，默认空字符串列表

        返回:
        str: 替换后的字符串
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

    @staticmethod
    def remove_at_user(content):
        """去除前面艾特的用户"""
        return re.sub(r'^(@[^\s@]+[\s]*)*', '', content)

    @staticmethod
    def extract_province_city(address):
        """
        从地址字符串中提取省份和城市（精确到地级市）
        规则：
        1. 优先匹配省份，再匹配该省份下的城市
        2. 未匹配到则返回空字符串
        3. 支持直辖市自动填充（如上海→上海市）

        :param: address -- 地址字符串
        :return: [省份, 城市]
        """
        # 中国省份列表（含简称）
        provinces = {
            '北京': ['北京市'],
            '上海': ['上海市'],
            '天津': ['天津市'],
            '重庆': ['重庆市'],
            '河北': ['石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水'],
            '山西': ['太原', '大同', '阳泉', '长治', '晋城', '朔州', '晋中', '运城', '忻州', '临汾', '吕梁'],
            '内蒙古': ['呼和浩特', '包头', '乌海', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布', '兴安', '锡林郭勒', '阿拉善'],
            '辽宁': ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛'],
            '吉林': ['长春', '吉林', '四平', '辽源', '通化', '白山', '松原', '白城', '延边'],
            '黑龙江': ['哈尔滨', '齐齐哈尔', '鸡西', '鹤岗', '双鸭山', '大庆', '伊春', '佳木斯', '七台河', '牡丹江', '黑河', '绥化', '大兴安岭'],
            '江苏': ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁'],
            '浙江': ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'],
            '安徽': ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', '滁州', '阜阳', '宿州', '六安', '亳州', '池州', '宣城'],
            '福建': ['福州', '厦门', '莆田', '三明', '泉州', '漳州', '南平', '龙岩', '宁德'],
            '江西': ['南昌', '景德镇', '萍乡', '九江', '新余', '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶'],
            '山东': ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '临沂', '德州', '聊城', '滨州', '菏泽'],
            '河南': ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店', '济源'],
            '湖北': ['武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州', '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州', '恩施', '潜江'],
            '湖南': ['长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底', '湘西'],
            '广东': ['广州', '韶关', '深圳', '珠海', '汕头', '佛山', '江门', '湛江', '茂名', '肇庆', '惠州', '梅州', '汕尾', '河源', '阳江', '清远', '东莞', '中山', '潮州', '揭阳', '云浮'],
            '广西': ['南宁', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左'],
            '海南': ['海口', '三亚', '三沙', '儋州'],
            '四川': ['成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳', '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州', '雅安', '巴中', '资阳', '阿坝','甘孜', '凉山'],
            '贵州': ['贵阳', '六盘水', '遵义', '安顺', '毕节', '铜仁', '黔西南', '黔东南', '黔南'],
            '云南': ['昆明', '曲靖', '玉溪', '保山', '昭通', '丽江', '普洱', '临沧', '楚雄', '红河', '文山', '西双版纳', '大理', '德宏', '怒江', '迪庆'],
            '西藏': ['拉萨', '日喀则', '昌都', '林芝', '山南', '那曲', '阿里'],
            '陕西': ['西安', '铜川', '宝鸡', '咸阳', '渭南', '延安', '汉中', '榆林', '安康', '商洛'],
            '甘肃': ['兰州', '嘉峪关', '金昌', '白银', '天水', '武威', '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南', '临夏', '甘南'],
            '青海': ['西宁', '海东', '海北', '黄南', '海南', '果洛', '玉树', '海西'],
            '宁夏': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
            '新疆': ['乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '昌吉', '博州', '巴州', '阿克苏', '克州', '喀什', '和田', '伊犁', '塔城', '阿勒泰', '石河子', '五家渠', '阿拉尔', '图木舒克', '可克达拉', '双河', '胡杨河', '北屯', '铁门关', '新星'],
            '台湾': ['台北', '新北', '桃园', '台中', '台南', '高雄', '基隆', '新竹', '嘉义'],
            '香港': ['香港'],
            '澳门': ['澳门']
        }

        # 标准化地址（去除空格和特殊字符）
        clean_addr = ''.join(filter(str.isprintable, address.strip()))

        # 遍历省份匹配
        for p, cities in provinces.items():
            # 在该省份下匹配城市
            for c in cities:
                if c in clean_addr:
                    city, province = c, p
                    # city = c + ('市' if not c.endswith('市') else '')
                    # if p in ['北京', '上海', '天津', '重庆']:
                    #     province = p
                    # elif p in ['香港', '澳门']:
                    #     city = c
                    #     province = p + '特别行政区'
                    # else:
                    #     province = p + '省'
                    return [province, city]

        # 未匹配到则返回空
        return ['', '']

    @staticmethod
    def add_stock_prefix(stock_code):
        """
        根据股票代码自动添加交易所前缀（支持多市场）
        市场判断规则：
        A股：6: SH | 0, 3: SZ | 4, 8, 9: BJ  长度=6
        B股：900/200开头（沪B/深B）或 SHB/SZB 前缀
       港股：5位数字或.HK结尾
       美股：1-5位字母或.US/.NYSE/.NASDAQ结尾
       中概股：特殊代码（如BABA）或.US结尾

        :param: stock_code -- 股票代码（支持int/str类型）
        :return: 带前缀的股票代码字符串
        """
        if not isinstance(stock_code, (str, int)):
            return stock_code

        code_str = str(stock_code).strip().upper()

        # 如果已有前缀，直接返回
        sgl = ['SHB', 'SZB', 'BJ', 'SH', 'SZ', 'HK', 'US', 'NYSE', 'NASDAQ', '.']
        if any(s in code_str for s in sgl):
            return code_str

        # 1. 检查B股（优先级最高）
        if (code_str.startswith(('900', '200')) and len(code_str) == 6) or \
                (len(code_str) == 3 and code_str.isdigit() and code_str.startswith(('9', '2'))):
            if code_str.startswith('900') or (len(code_str) == 3 and code_str.startswith('9')):
                code_str = f"SHB{code_str[-3:]}" if len(code_str) == 6 else f"SHB{code_str}"
            elif code_str.startswith('200') or (len(code_str) == 3 and code_str.startswith('2')):
                code_str = f"SZB{code_str[-3:]}" if len(code_str) == 6 else f"SZB{code_str}"
            return code_str

        # 2. 检查A股
        if len(code_str) == 6 and code_str.isdigit():
            if code_str[0] == '6':
                code_str = f"SH{code_str}"
            elif code_str[0] in ('0', '3'):
                code_str = f"SZ{code_str}"
            elif code_str[0] in ('4', '8', '9'):
                code_str = f"BJ{code_str}"
            return code_str

        # 3. 检查港股（5位数字或.HK结尾）
        if (len(code_str) == 5 and code_str.isdigit()) or code_str.endswith('.HK'):
            return code_str.split('.')[0] + '.HK'

        # 4. 检查美股（字母或.US/.NYSE结尾）
        if code_str.isalpha() or any(code_str.endswith(ext) for ext in ('.US', '.NYSE', '.NASDAQ')):
            return code_str.split('.')[0] + '.US'

        # 5. 中概股特殊处理（如BABA->BABA.US）
        if len(code_str) <= 5 and code_str.isalpha():
            return f"{code_str}.US"

        # 无法识别则原样返回
        return code_str

    @staticmethod
    def remove_stock_prefix(stock_symbol):
        """去除市场标识"""
        stock_symbol = str(stock_symbol).upper()
        sgl = ['SHB', 'SZB', 'BJ', 'SH', 'SZ', 'HK', 'US', 'NYSE', 'NASDAQ', '.']
        return Str.replace_multiple(stock_symbol, sgl)

    @staticmethod
    def get_stock_prefix(stock_code):
        """获取市场标识"""
        stock_code = Str.remove_stock_prefix(stock_code)
        stock_symbol = Str.add_stock_prefix(stock_code)
        return stock_symbol.replace(stock_code, '').replace('.', '')
