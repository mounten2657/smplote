import re
import os
from typing import Union, Dict, Optional, Any


class Env:
    @staticmethod
    def load(
            env_path: str = ".env",
            encoding: str = "utf-8",
            override: bool = False
    ) -> Dict[str, str]:
        """
        加载 .env 文件配置到环境变量
        :param env_path: 文件路径，默认当前目录的 .env
        :param encoding: 文件编码，默认 utf-8
        :param override: 是否覆盖已存在的环境变量
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
            env_path: str = ".env"
    ) -> Union[str, int, bool, None]:
        """
        获取配置值（优先从环境变量读取）
        :param key: 要获取的键名
        :param default: 默认值（支持自动类型转换）
        :param env_path: 自定义 .env 文件路径
        :return: 配置值（自动尝试类型转换）
        """
        # 先尝试从环境变量获取
        value = os.getenv(key)
        if value is not None:
            return Env._convert_type(value)

        # 环境变量不存在则尝试从 .env 文件加载
        Env.load(env_path)
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
    def convert_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        替换配置中的[ENV.XXX|default]占位符
        :param config_data: 原始配置字典
        :return: 替换后的完整配置
        """
        def _replace_placeholder(value: Any) -> Any:
            if isinstance(value, str):
                # 匹配 [ENV.XXX|default] 或 [ENV.XXX] 格式
                match = re.fullmatch(r'\[ENV\.([^\|\]]+)(?:\|([^\]]+))?\]', value.strip())
                if match:
                    env_key, default_value = match.groups()
                    # 获取环境变量值，不存在则使用默认值（默认值可能为None）
                    return Env.get(env_key, default_value) or default_value
            return value

        def _process(data: Any) -> Any:
            if isinstance(data, dict):
                return {k: _process(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [_process(item) for item in data]
            else:
                return _replace_placeholder(data)

        return _process(config_data)

