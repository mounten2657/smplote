import os
import re
import urllib.parse
import base64
import requests
from urllib.request import urlretrieve
from tool.core.dir import Dir
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


class Emoji:

    EMOJI_CDN_URL = 'https://emojicdn.elk.sh'
    EMOJI_STYLE = 'twitter'  # twitter 方形 | apple 圆角
    EMOJI_CACHE_DIR = Dir.abs_dir(f'data/static/emoji/emojicdn_elk_sh/{EMOJI_STYLE}')
    if not os.path.exists(EMOJI_CACHE_DIR):
        os.makedirs(EMOJI_CACHE_DIR, exist_ok=True)

    def __init__(self):
        pass

    @staticmethod
    def replace_emoji_to_img(text):
        """
        检测文本中的表情符号并替换为<img>标签
        :param text: 原始文本（Markdown或HTML）
        :return: 替换后的文本
        """
        # 使用emoji库精确识别
        def replace_with_img(match):
            emoji_char = match.group()  # eg: emoji_char = 🥑 , preg matched \U0001F951
            emoji_hex_list = [f"{ord(c):x}" for c in emoji_char]  # 有可能是组合表情: ❤️-> ['2764', 'fe0f']
            img_str = ''
            for eh in emoji_hex_list:
                if eh == 'fe0f':  # 跳过连接符
                    continue
                emoji_path = Emoji.get_emoji_local_path(eh)
                emoji_base64 = Emoji.image_to_base64(emoji_path)
                # emoji_path = Emoji.path_to_file_uri(emoji_path)
                # img_str += f'<img src="{emoji_path}" width="20" height="20" alt="{emoji_char}">'
                img_str += f'<img src="data:image/png;base64,{emoji_base64}" width="18" height="18" alt="{emoji_char}">'
            return img_str
        # 匹配所有表情符号（包括Unicode 15.0新表情）
        emoji_pattern = re.compile(
            r"["
            r"\U0001F300-\U0001FAD6"  # 常规表情范围
            r"\U0001F004-\U0001F0CF"
            r"\U0001F170-\U0001F251"
            r'\U0001F680-\U0001F6FF'
            r'\U0001F1E0-\U0001F1FF'
            r'\U00002600-\U000026FF'
            r'\U00002702-\U000027B0'
            r'\U0000E000-\U0000F8FF'
            r'\U0001F900-\U0001F9FF'
            r'\U0001FA70-\U0001FAFF'
            # r'\U000024C2-\U0001F251'  # 意义不明，暂时注释
            r"\u200d"  # 零宽度连接符（用于组合表情）
            r"\uFE0F"  # 变体选择符
            r"]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(replace_with_img, text)

    @staticmethod
    def get_emoji_local_path(emoji_char):
        emoji_hex = emoji_char.lower() # eg: 1F951 -> 1f951
        default_path = f"{Emoji.EMOJI_CACHE_DIR}/2753.png"  # 2753 红问号 | 2754 白问号
        local_path = f"{Emoji.EMOJI_CACHE_DIR}/{emoji_hex}.png"
        if not os.path.exists(local_path):
            try:
                emoji_trans = Emoji.s_unicode_to_utf8_hex(emoji_hex)  # 1f951 -> %F0%9F%A5%91
                urlretrieve(
                    f"{Emoji.EMOJI_CDN_URL}/{emoji_trans}?style={Emoji.EMOJI_STYLE}",
                    local_path
                )
            except:
                local_path = default_path
        return local_path

    @staticmethod
    def unicode_to_utf8_hex(code_point):
        """
        将 Unicode 码点转换为 UTF - 8 编码的十六进制表示
        :param code_point: Unicode 码点，如 0x1F951
        :return: UTF - 8 编码的十六进制表示，如 %F0%9F%A5%91
        """
        char = chr(int(code_point, 16))
        utf8_bytes = char.encode('utf-8')
        hex_string = ''.join(f'%{byte:02X}' for byte in utf8_bytes)
        return hex_string

    @staticmethod
    def s_unicode_to_utf8_hex(emoji_hex):
        """
        将 Unicode 码点转换为 UTF - 8 编码的十六进制表示
        :param emoji_hex: 简版 Unicode 码点，如 1f951
        :return: UTF - 8 编码的十六进制表示，如 %F0%9F%A5%91
        """
        return Emoji.unicode_to_utf8_hex('0x' + emoji_hex.upper())

    @staticmethod
    def utf8_hex_to_unicode(utf8_hex):
        """
        将十六进制表示的 UTF - 8 编码转换为 Unicode 码点
        :param utf8_hex: 十六进制表示的 UTF - 8 编码，如 %F0%9F%A5%91
        :return: Unicode 码点，如 0x1F951
        """
        # 去除 % 符号
        pure_hex = utf8_hex.replace('%', '')
        # 将十六进制字符串转换为字节对象
        utf8_bytes = bytes.fromhex(pure_hex)
        # 对字节对象进行 UTF - 8 解码
        char = utf8_bytes.decode('utf-8')
        # 获取 Unicode 码点
        code_point = ord(char)
        return code_point

    @staticmethod
    def path_to_file_uri(path):
        # 先将反斜杠替换为正斜杠
        path = path.replace('\\', '/')
        # 分割路径，获取盘符和后面的路径
        if ':' in path:
            drive, rest_path = path.split(':', 1)
            # 对除盘符和冒号外的部分进行编码
            encoded_rest_path = urllib.parse.quote(rest_path)
            # 拼接成完整的 URI
            file_uri = f'file://{drive}:{encoded_rest_path}'
        else:
            # 如果没有盘符，直接编码路径
            encoded_path = urllib.parse.quote(path)
            file_uri = f'file://{encoded_path}'
        return file_uri

    @staticmethod
    def image_to_base64(image_path):
        try:
            # 以二进制模式打开图片文件
            with open(image_path, 'rb') as image_file:
                # 读取图片文件内容
                image_data = image_file.read()
                # 将图片数据转换为 Base64 编码
                base64_encoded = base64.b64encode(image_data).decode('utf-8')
                return base64_encoded
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def download_emoji(emoji_hex):
        emoji_hex = emoji_hex.lower()  # 1F951 -> 1f951
        save_dir = Emoji.EMOJI_CACHE_DIR
        emoji_trans = Emoji.s_unicode_to_utf8_hex(emoji_hex)  # 1f951 -> %F0%9F%A5%91
        url = f"{Emoji.EMOJI_CDN_URL}/{emoji_trans}?style={Emoji.EMOJI_STYLE}"
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            with open(f"{save_dir}/{emoji_hex}.png", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            print(f"Failed to download {emoji_hex}: {str(e)}")

    @staticmethod
    def download_all_emojis():
        # Unicode Emoji Ranges (更新至Unicode 15.0)
        ranges = [
            (0x1F300, 0x1FAD6),  # 常规表情
            (0x1F004, 0x1F0CF),  # 扑克/象棋等
            (0x1F170, 0x1F251),  # 字母符号
            (0x2600, 0x26FF),  # 杂项符号
            (0x2700, 0x27BF),  # 装饰符号
            (0xFE00, 0xFE0F),  # 变体选择符
            (0x1F900, 0x1F9FF),  # 补充符号
            (0x1FA70, 0x1FAFF)  # 扩展符号
        ]
        os.makedirs("emojis", exist_ok=True)
        emoji_hexes = set()
        # 生成所有可能的Unicode编码
        for start, end in ranges:
            for code in range(start, end + 1):
                # 跳过无效区域
                if 0x1F7EB <= code <= 0x1F7F0:
                    continue
                emoji_hexes.add(hex(code)[2:].upper())
        # 添加组合表情的分割符（零宽度连接符）
        emoji_hexes.add("200D")
        # 多线程下载（限制并发数避免被封）
        with ThreadPoolExecutor(max_workers=10) as executor:
            list(tqdm(
                executor.map(Emoji.download_emoji, emoji_hexes),
                total=len(emoji_hexes),
                desc="Downloading Emojis"
            ))
        return True

