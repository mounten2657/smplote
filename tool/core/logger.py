import os
import logging
import sys
import json
from flask import request
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from tool.core.dir import Dir
from tool.core.config import Config
from tool.core.str import Str
from tool.core.attr import Attr
from tool.core.http import Http


class Logger:
    _instance = None  # 单例模式，避免重复实例化
    _loggers = {}  # 用于缓存不同 log_name 的日志记录器

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        self.logger_dir = Dir.root_dir()
        self.config = Config.logger_config()
        self.uuid = Str.uuid()

    def setup_logger(self, log_type, log_name):
        logger_key = f"{log_type}_{log_name}"
        if logger_key in self._loggers:
            return self._loggers[logger_key]

        logger = logging.getLogger(f'{__name__}.{log_type}.{log_name}')
        log_level = self.config.get('log_level', 'DEBUG')
        logger.setLevel(getattr(logging, log_level))

        today = datetime.now().strftime('%Y%m%d')
        log_dir = os.path.join(self.logger_dir, self.config.get('log_path', 'storage/logs'), today)
        os.makedirs(log_dir, exist_ok=True)

        log_name = log_name if log_name else self.config.get('log_name_default', 'app')
        log_file = os.path.join(log_dir, f'{log_name}_{log_type}_{today}.log')

        file_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=7, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))

        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    'timestamp': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'uuid': getattr(record, 'uuid', None),
                    'msg': getattr(record, 'msg', None)
                }
                if log_type == 'http':
                    log_record.update({
                        'ip': getattr(record, 'ip', None),
                        'route': getattr(record, 'route', None),
                        'method': getattr(record, 'method', None),
                        'status_code': getattr(record, 'status_code', None),
                        'user_agent': getattr(record, 'user_agent', None),
                        'authcode': getattr(record, 'authcode', None),
                        'data': getattr(record, 'data', None),
                        'request_params': getattr(record, 'request_params', None),
                        'response_result': getattr(record, 'response_result', None)
                    })
                else:
                    log_record.update({
                        'command': getattr(record, 'command', None),
                        'data': getattr(record, 'data', None)
                    })
                return json.dumps(log_record, ensure_ascii=False)

        formatter = JsonFormatter()
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        self._loggers[logger_key] = logger
        return logger

    def get_extra_data(self, data=None):
        if Http.is_http_request():
            # 尝试获取 HTTP 请求信息，如果能获取到说明是 HTTP 请求
            ip = request.remote_addr
            route = request.path
            method = request.method
            headers = json.loads(json.dumps(dict(request.headers), ensure_ascii=False, indent=4))
            user_agent = Attr.get_attr(headers, 'User-Agent')
            authcode = Attr.get_attr(headers, 'authcode', '')
            request_params = dict(request.args)
            response = Attr.get_attr(data, 'response')
            status_code = Attr.get_attr(response, 'status_code', 100)
            response_result = Attr.get_attr(response, 'response_result')
            extra = {
                'uuid': self.uuid,
                'ip': ip,
                'route': route,
                'method': method,
                'status_code': status_code,
                'user_agent': user_agent,
                'authcode': authcode,
                'data': Attr.remove_keys(data, ['request', 'response']),
                'request_params': request_params,
                'response_result': response_result
            }
        else:
            # 若获取不到 HTTP 请求信息，说明是命令行执行
            # command_parts = [sys.executable] + sys.argv  # 这获取的是绝对路径
            # command = " ".join(command_parts)                # 太长了， 直接写死成 python
            command = "python " + " ".join(sys.argv)
            extra = {
                'uuid': self.uuid,
                'command': command,
                'data': data
            }
        return extra

    def write(self, data=None, msg="", log_name="app", log_level='info'):
        extra = self.get_extra_data(data)
        log_type = 'http' if Http.is_http_request() else 'command'
        logger_handle = self.setup_logger(log_type, log_name)
        method = getattr(logger_handle, log_level.lower())
        method(msg, extra=extra)

    def debug(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'debug')

    def info(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'info')

    def warning(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'warning')

    def error(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'error')

    def exception(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'exception')


