import re
import os
from pathlib import Path
from typing import Union, Dict, Optional, Any
from tool.core.dir import Dir


class Env:

    # 自定义 .env 文件路径
    _env_path = Dir.abs_dir('.env')

    @staticmethod
    def load(
            env_path: str = _env_path,
            override: bool = False,
            encoding: str = "utf-8"
    ) -> Dict[str, str]:
        """
        加载 .env 文件配置到环境变量
        :param env_path: 文件路径，默认当前目录的 .env
        :param override: 是否覆盖已存在的环境变量
        :param encoding: 文件编码，默认 utf-8
        :return: 解析后的键值对字典
        """
        env_dict = {}
        try:
            with open(env_path, "r", encoding=encoding) as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith("#"):
                        continue
                    # 分割键值对
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")  # 去除引号

                    # 存储到字典并设置环境变量
                    env_dict[key] = value
                    if override or key not in os.environ:
                        os.environ[key] = value
        except FileNotFoundError:
            pass  # 文件不存在时静默跳过
        return env_dict

    @staticmethod
    def get(
            key: str,
            default: Optional[Union[str, int, bool]] = None,
            env_path: str = _env_path,
            override: bool = False
    ) -> Union[str, int, bool, None]:
        """
        获取配置值（优先从环境变量读取）
        :param key: 要获取的键名
        :param default: 默认值（支持自动类型转换）
        :param env_path: 自定义 .env 文件路径
        :param override: 是否重载环境变量
        :return: 配置值（自动尝试类型转换）
        """
        override and Env.load(env_path, True)
        # 先尝试从环境变量获取
        value = os.getenv(key)
        if value is not None:
            return Env._convert_type(value)

        # 环境变量不存在则尝试从 .env 文件加载
        not override and Env.load(env_path)
        value = os.getenv(key)
        if value is not None:
            return Env._convert_type(value)

        # 返回默认值（同样做类型转换）
        return Env._convert_type(default) if default is not None else None

    @staticmethod
    def _convert_type(value: Union[str, int, bool, None]) -> bool | int | float | str | None:
        """尝试将字符串值转换为更合适的类型"""
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    pass
        return value

    @staticmethod
    def convert_config(config_data: Dict[str, Any], env_path: str = _env_path) -> Dict[str, Any]:
        """
        替换配置中的[ENV.XXX|default]占位符
        :param config_data: 原始配置字典
        :param env_path: 自定义 .env 文件路径
        :return: 替换后的完整配置
        """
        def _replace_placeholder(value: Any) -> Any:
            if isinstance(value, str):
                # 匹配 [ENV.XXX|default] 或 [ENV.XXX] 格式
                match = re.fullmatch(r'\[ENV\.([^\|\]]+)(?:\|([^\]]+))?\]', value.strip())
                if match:
                    env_key, default_value = match.groups()
                    # 获取环境变量值，不存在则使用默认值（默认值可能为None）
                    return Env.get(env_key, default_value, env_path, True) or default_value
            return value

        def _process(data: Any) -> Any:
            if isinstance(data, dict):
                return {k: _process(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [_process(item) for item in data]
            else:
                return _replace_placeholder(data)

        return _process(config_data)

    @staticmethod
    def write_env(key: str, value: Any, env_file: str = _env_path, encoding = 'utf-8') -> bool:
        """
        安全写入.env文件配置项
        Args:
            key: 要写入的键名（如"APP_ID"）
            value: 要设置的值
            env_file: .env文件路径（默认当前目录）
            encoding: .env文件编码（默认utf-8）

        Returns:
            bool: 是否成功写入（False表示键不存在或被注释）
        """
        path = Path(env_file)
        if not path.exists():
            return False

        # 读取文件内容
        try:
            with open(path, 'r', encoding=encoding) as f:
                lines = f.readlines()
        except Exception:
            return False

        key_exists = False
        key_pattern = re.compile(rf'^\s*{re.escape(key)}\s*=[\s"]*(.*?)[\s"]*$')
        comment_pattern = re.compile(rf'^\s*#\s*{re.escape(key)}\s*=')

        new_lines = []
        for line in lines:
            # 检查是否为注释状态的键
            if comment_pattern.match(line):
                continue

            # 检查是否为目标键
            match = key_pattern.match(line)
            if match:
                key_exists = True
                # 找到匹配的键，更新值
                new_line = f'{key}={value}\n'
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        # 如果键不存在
        if not key_exists:
            return False

        # 写入文件
        try:
            with open(path, 'w', encoding=encoding) as f:
                f.writelines(new_lines)
            return True
        except Exception:
            return False


