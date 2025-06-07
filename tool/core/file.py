import os
import json
import base64
from pathlib import Path
from typing import Union, Any, Optional
from tool.core.attr import Attr
from tool.core.dir import Dir
from tool.core.str import Str


class File:

    @staticmethod
    def enc_dir(file_path, root_dir='wechat'):
        """获取加密路径"""
        file_path = str(file_path).replace(root_dir, '')
        base_path, file_ext = str(file_path).rsplit('.', 1)
        file_ext = file_ext if 'silk' != file_ext else 'mp3'
        enc = Str.encrypt_str(base_path[::-1])
        dir_path = f"/{enc[0:2].upper()}/{enc[2:4].upper()}/{enc[4:6].upper()}"
        return f"{dir_path}/{enc[6:][::-1]}.{file_ext}"

    @staticmethod
    def des_dir(file_path, root_dir='wechat'):
        """获取解密路径"""
        file_path = str(file_path).replace(root_dir, '')
        base_path, file_ext = str(file_path).rsplit('.', 1)
        try:
            base_path = f"{base_path[:9]}{base_path[9:][::-1]}"
            des = Str.decrypt_str(str(base_path).replace('/', ''))
            return f"{root_dir}{des[::-1]}.{file_ext}"
        except:
            # raise ValueError('不是有效的路径')
            return ''

    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[Union[dict, list, str]]:
        """
        读取文件内容，自动处理JSON格式和普通文本
        :param file_path: 文件路径
        :param encoding: 文件编码，默认utf-8
        :return: 文件内容（JSON会被解析为dict/list，普通文本为str），出错返回None
        """
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            return None
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read().strip()
                # 尝试解析JSON
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return content
        except Exception as e:
            return None

    @staticmethod
    def save_file(content: Any, save_path: str, file_append: bool = False, new_line = True, encoding: str = 'utf-8') -> bool:
        """
        保存内容到文件，自动处理多种数据类型
        :param content: 要保存的内容（支持dict/list/str等）
        :param save_path: 保存路径
        :param file_append: 是否追加模式，默认False
        :param new_line: 是否换行模式，默认True
        :param encoding: 文件编码，默认utf-8
        :return: 成功返回True，失败返回False
        """
        if os.path.isdir(save_path):
            return False
        try:
            mode = 'a' if file_append else 'w'
            # 自动创建不存在的目录
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            # 处理不同类型的内容
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False, indent=4)
            with open(save_path, mode, encoding=encoding) as f:
                f.write(str(content))
                if new_line and not content.endswith('\n'):  # 确保内容以换行结尾
                    f.write('\n')
            return True
        except Exception as e:
            return False

    @staticmethod
    def exists(fp):
        """判断文件或路径是否存在"""
        return os.path.exists(fp)

    @staticmethod
    def deduplicate_json_file(input_file, key):
        """对json文件里的列表去重并重新写入"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 列表去重
        result = Attr.deduplicate_list(data, key)
        # 重新写入文件
        if result:
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=4)
        return result

    @staticmethod
    def convert_to_abs_path(data, dir_key_name, base_dir=None):
        """递归将字典中所有 指定目录键名 的值转为绝对路径"""
        if base_dir is None:
            base_dir = Dir.root_dir()
        if isinstance(data, dict):
            for key, value in data.items():
                if key == dir_key_name:
                    data[key] = os.path.abspath(os.path.join(base_dir, value))
                elif isinstance(value, (dict, list)):
                    File.convert_to_abs_path(value, dir_key_name, base_dir)
        elif isinstance(data, list):
            for item in data:
                File.convert_to_abs_path(item, dir_key_name, base_dir)
        return data

    @staticmethod
    def is_safe_path(basedir, path):
        """检查路径是否在允许的目录内"""
        basedir = os.path.abspath(basedir)
        request_path = os.path.abspath(os.path.join(basedir, path))
        return os.path.commonpath([basedir, request_path]) == basedir

    @staticmethod
    def get_file_mtime(file_path):
        """获取文件最近的修改时间 - 整数时间戳"""
        file_path = Path(file_path)
        if not file_path.exists():
            return 0
        return int(file_path.stat().st_mtime)

    @staticmethod
    def get_base64(file_path: str) -> str:
        """
        将本地文件转换为 Base64 编码字符串

        参数:
        file_path (str): 本地文件路径

        返回:
        str: 图片的 Base64 编码字符串（不含前缀）

        示例:
         get_base64("path/to/image.jpg")
        'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA...'
        """
        try:
            with open(file_path, "rb") as fp:
                # 读取文件内容并进行 Base64 编码
                encoded_bytes = base64.b64encode(fp.read())
                # 转换为 UTF-8 字符串
                return encoded_bytes.decode("utf-8")
        except FileNotFoundError:
            raise ValueError(f"文件不存在: {file_path}")
        except Exception as e:
            raise RuntimeError(f"转Base64失败: {str(e)}")

    # @staticmethod
    # def get_mp3_duration(file_path):
    #     """获取mp3文件时长"""
    #     from pydub import AudioSegment
    #     audio = AudioSegment.from_file(file_path, "mp3")
    #     duration_ms = len(audio)  # 获取时长（毫秒）
    #     duration_sec = duration_ms / 1000  # 转换为秒
    #     return duration_sec
