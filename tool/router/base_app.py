import threading
from typing import Dict, Any, Optional
from tool.core import *
from tool.router import *


class BaseApp:

    _instance: Optional['BaseApp'] = None  # 单例模式，避免重复实例化
    _instance_lock = threading.Lock()           # 保证多线程环境下单例的唯一性，避免竞态条件
    _http_method = None
    _method_name = None
    _rule_list = None
    _logger = None

    def __new__(cls, **kwargs):
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.__init__(**kwargs)
        return cls._instance

    def __init__(self, **kwargs):
        self.args = kwargs
        self.root_dir = Dir.root_dir()
        self.params = self.get_params()
        self.validate()

    def __reduce__(self):
        return self.__class__, ()

    @classmethod
    def get_params(cls) -> Dict[str, Any]:
        if not Http.is_http_request():
            return ParseHandler.get_command_params()
        return RouterHandler.get_http_params()

    @property
    def http_method(self):
        self._http_method = Http.get_request_method()
        return self._http_method

    @property
    def method_name(self):
        if not Http.is_http_request():
            return ParseHandler.get_method_name()
        return RouterHandler.get_method_name()

    @property
    def logger(self):
        if not self._logger:
            self._logger = Logger()
        return self._logger

    def validate(self):
        validate = Validator()
        rule_list = Attr.get(self._rule_list, self.method_name, {})
        method_allow_list = Attr.get(rule_list, 'method', ['GET', 'POST'])
        method_allow_list.append('COMMAND')
        message = Attr.get(rule_list, 'message', None)
        # 验证请求方式
        if rule_list and self.http_method not in method_allow_list:
            Error.throw_exception(f'Method Not Allow - [{self.http_method}]', 405)
        # 验证参数正确性
        if rule_list and not validate.check(self.params, rule_list['rule'], message):
            Error.throw_exception(validate.err_msg, validate.err_code)

    @classmethod
    def success(cls, data=None, msg='success', code=0):
        return Api.success(data, msg, code)

    @classmethod
    def error(cls, msg='error', data=None, code=999):
        return Api.error(msg, data, code)



