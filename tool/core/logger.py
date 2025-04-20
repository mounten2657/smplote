import os
import logging
import re
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
from tool.core.time import Time


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
        self.log_level = self.config.get('log_level', 'DEBUG')
        self.recode_debug = int(self.config.get('log_recode_debug', '0'))
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
            @staticmethod
            def extract_runtime(input_str: str):
                """
                提取 [RT.{run_time}] 中的 run_time，并移除该部分
                :param input_str: 输入字符串，如 "END[RT.12.34]"
                :return: (清理后的字符串, run_time 的值) 如 ("END", "12.34")
                """
                # 匹配 [RT.xxx] 并提取 xxx
                pattern = r'\[RT\.([^\]]+)\]'  # 匹配 [RT.xxx]，并捕获 xxx
                match = re.search(pattern, input_str)
                if match:
                    run_time = match.group(1)  # 提取 run_time
                    cleaned_str = re.sub(pattern, '', input_str)  # 移除 [RT.xxx]
                    return cleaned_str.strip(), run_time
                else:
                    return input_str, None  # 如果没有匹配到，返回原字符串和 None

            def format(self, record):
                msg = getattr(record, 'msg', '')
                msg, run_time = self.extract_runtime(msg)
                log_record = {
                    'timestamp': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'uuid': getattr(record, 'uuid', None),
                    'msg': msg
                }
                if run_time:
                    run_time = run_time if re.match(r"^-?\d+$",  run_time) else round(float(run_time), 13)
                    log_record.update({"run_time": run_time})
                if log_type == 'http':
                    log_record.update({
                        'ip': getattr(record, 'ip', None),
                        'route': getattr(record, 'route', None),
                        'method': getattr(record, 'method', None),
                        'status_code': getattr(record, 'status_code', None),
                        'user_agent': getattr(record, 'user_agent', None),
                        'content_type': getattr(record, 'content_type', None),
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
            content_type = Attr.get_attr(headers, 'Content-Type')
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
                'content_type': content_type,
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
        if not self.recode_debug and log_level.upper() in ['DEBUG', 'INFO']:
            return self.color_print(data, msg, log_level)
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

    def color_print(self, data, msg="NULL", log_level="debug"):
        log_level = log_level.upper()
        color = '31m'  # 31m - red | 32m - green | 33m - yellow | 34 blue | 36m cyan
        if log_level == "DEBUG":
            color = '32m'
        if log_level == "WARNING":
            color = '33m'
        if log_level == "INFO":
            color = '36m'
        text = f"[{Time.date()}] - {log_level} - {msg} - {data}"[:383]
        print(f"\033[{color}{text}\033[0m")
        return True
