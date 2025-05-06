import re
import json
import datetime
from typing import Dict, Any, Optional
from tool.core.api import Api


class Validator:
    """自定义的参数验证器"""

    _ERR_CODE = 899  # 默认错误码

    def __init__(self):
        self._init_err_data()
        # 注册自定义验证器
        self._validators = {
            'required': self._validate_required,
            'int': self._validate_int,
            'float': self._validate_float,
            'string': self._validate_string,
            'min': self._validate_min,
            'max': self._validate_max,
            'in': self._validate_in,
            'json': self._validate_json,
            'url': self._validate_url,
            'mobile': self._validate_mobile,
            'timestamp': self._validate_timestamp,
            'date_format': self._validate_date_format,
            'required_with': self._validate_required_with,
        }

    def _init_err_data(self):
        """初始化错误信息"""
        self.err_code = self._ERR_CODE
        self.err_msg = ""
        self.err_msg_list = {}
        self.err_data = {}

    def check(self, data: Optional[Dict], rules: Dict[str, Any], custom_messages: Optional[Dict] = None) -> bool:
        """
        执行验证
        :param data: 要验证的数据(默认为空时使用类属性)
        :param rules: 验证规则
        :param custom_messages: 自定义的报错信息
        :return: 验证通过返回True，失败返回False并设置错误信息
        """
        if custom_messages is None:
            custom_messages = {}
        if data is None:
            data = self.__dict__  # 如果没有传入数据，验证类自身属性

        self._init_err_data()
        for field, rule_str in rules.items():
            value = data.get(field)
            rules_parts = rule_str.split('|')

            for rule in rules_parts:
                if ':' in rule:
                    rule_name, *rule_args = rule.split(':')
                    rule_args = ':'.join(rule_args)  # 处理带冒号的参数(如date_format)
                else:
                    rule_name, rule_args = rule, None

                if rule_name not in self._validators:
                    continue  # 跳过不支持的规则

                is_valid = self._validators[rule_name](value, rule_args, field, data)

                if not is_valid:
                    # 获取自定义错误消息
                    custom_key = f"{field}.{rule_name}"
                    # default_msg = f"`{field}` validate failed: [{rule}]"
                    default_msg = f"`{field}` 参数验证失败: [{rule}]"
                    error_msg = custom_messages.get(custom_key) or custom_messages.get(field) or default_msg
                    self.err_msg_list[field] = {
                        'rule': rule,
                        'value': value,
                        'message': error_msg
                    }
                    if not self.err_msg:
                        self.err_msg = error_msg
                    self.err_data = Api.restful(self.err_msg_list, self.err_msg, self.err_code)
                    return False

        return True

    # ---------- 内置验证器 ----------
    def _validate_required(self, value: Any, *_) -> bool:
        """必填验证"""
        return value is not None and value != ""

    def _validate_int(self, value: Any, *_) -> bool:
        """整数验证"""
        if value is None:
            return True  # 非required的可以为空
        return isinstance(value, int) or (isinstance(value, str) and value.isdigit())

    def _validate_float(self, value: Any, *_) -> bool:
        """浮点数验证"""
        if value is None:
            return True
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    def _validate_string(self, value: Any, *_) -> bool:
        """字符串验证"""
        if value is None:
            return True
        if isinstance(value, str):
            try:
                float(value)
                return False
            except ValueError:
                return True
        return False

    def _validate_min(self, value: Any, min_val: str, *_) -> bool:
        """最小值验证"""
        if value is None:
            return True
        try:
            min_val = int(min_val) if '.' not in min_val else float(min_val)
            if self._validate_string(value):
                return len(value) >= min_val
            value = int(value) if isinstance(value, str) and value.isdigit() else value
            return float(value) >= min_val
        except (ValueError, TypeError):
            return False

    def _validate_max(self, value: Any, max_val: str, *_) -> bool:
        """最大值验证"""
        if value is None:
            return True
        try:
            max_val = int(max_val) if '.' not in max_val else float(max_val)
            if self._validate_string(value):
                return len(value) <= max_val
            value = int(value) if isinstance(value, str) and value.isdigit() else value
            return float(value) <= max_val
        except (ValueError, TypeError):
            return False

    def _validate_in(self, value: Any, in_str: str,  *_) -> bool:
        """In验证"""
        if value is None:
            return True
        return value in str(in_str).split(',')

    def _validate_json(self, value: Any, *_) -> bool:
        """JSON验证"""
        if value is None:
            return True
        if isinstance(value, (dict, list)):
            return True
        if not isinstance(value, str):
            return False
        try:
            res = json.loads(value)
            return isinstance(res, (dict, list))
        except ValueError:
            return False

    def _validate_url(self, value: Any, *_) -> bool:
        """URL验证"""
        if value is None:
            return True
        pattern = re.compile(
            r'^(?:http|ftp)s?://'  # http:// 或 https:// 或 ftp:// 或 ftps://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # 域名
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP 地址
            r'(?::\d+)?'  # 可选的端口号
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(pattern.match(value))

    def _validate_mobile(self, value: Any, *_) -> bool:
        """手机号验证(中国)"""
        if value is None:
            return True
        pattern = r'^1[3-9]\d{9}$'
        return bool(re.match(pattern, str(value)))

    def _validate_timestamp(self, value: Any, *_) -> bool:
        """时间戳验证"""
        if value is None:
            return True
        try:
            if isinstance(value, str) and not value.isdigit():
                return False
            timestamp = int(value)
            datetime.datetime.fromtimestamp(timestamp)
            return True
        except (ValueError, TypeError, OSError):
            return False

    def _validate_date_format(self, value: Any, fmt: str, *_) -> bool:
        """日期格式验证"""
        if value is None:
            return True
        try:
            datetime.datetime.strptime(str(value), fmt)
            return True
        except ValueError:
            return False

    def _validate_required_with(self, value: Any, other_field: str, field: str, data: Dict) -> bool:
        """依赖字段验证"""
        if other_field not in data.keys() or data[other_field] is None:
            return True  # 被依赖字段不存在时跳过验证
        return self._validate_required(value)

    # ---------- 扩展方法 ----------
    def add_validator(self, name: str, validator_func: callable):
        """
        添加自定义验证器
        validator = Validator()
        validator.add_validator('even', lambda v, *_: v % 2 == 0)
        rules = {"number": "required|int|even"}
        if not validator.validate(data, rules):
            print(validator.err_msg)
        """
        self._validators[name] = validator_func

    def validate(self, data: Dict, rules: Dict, messages: Optional[Dict] = None) -> bool:
        """快捷验证方法 - 别名"""
        return self.check(data, rules, messages or {})
