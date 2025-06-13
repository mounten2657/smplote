import os
import logging
import re
import sys
import json
from flask import request
from queue import Queue
from threading import Lock
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from tool.core.dir import Dir
from tool.core.config import Config
from tool.core.str import Str
from tool.core.attr import Attr
from tool.core.http import Http
from tool.core.transfer import Transfer

# 全局日志队列和锁
log_queue = Queue()
log_lock = Lock()
log_listener_active = 1

# 限制日志队列大小（避免内存溢出）
MAX_LOG_QUEUE_SIZE = 1000


class Logger:

    _instance = None  # 单例模式，避免重复实例化
    _loggers = {}  # 用于缓存不同 log_name 的日志记录器

    # 定义不同日志级别的颜色代码
    # 低亮 31m - red | 32m - green | 33m - yellow | 34 blue | 36m cyan
    # 高亮 91m - red | 92m - green | 93m - yellow | 94 blue | 96m cyan
    COLORS_LOWER = {
        'DEBUG': '\033[32m',
        'INFO': '\033[36m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[41m'
    }
    COLORS_LIGHT = {
        'DEBUG': '\033[92m',
        'INFO': '\033[96m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[41m'
    }
    RESET = '\033[0m'

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        self.logger_dir = Dir.root_dir()
        self.config = Config.logger_config()
        self.log_level = self.config.get('log_level', 'DEBUG')
        self.display_json = int(self.config.get('log_display_json', '0'))
        self.display_light = int(self.config.get('log_display_light', '0'))
        self.display_colors = self.COLORS_LIGHT if self.display_light else self.COLORS_LOWER
        self.uuid = Str.uuid()
        self.log_queue = log_queue
        self.log_lock = log_lock

    def setup_logger(self, log_type, log_name):
        logger_key = f"{log_type}_{log_name}"
        if logger_key in self._loggers:
            return self._loggers[logger_key]

        logger = logging.getLogger(f'{__name__}.{log_type}.{log_name}')
        log_level = self.config.get('log_level', 'DEBUG')
        logger.setLevel(getattr(logging, log_level))
        display_colors = self.display_colors

        today = datetime.now().strftime('%Y%m%d')
        log_dir = os.path.join(self.logger_dir, self.config.get('log_path', 'storage/logs'), today)
        os.makedirs(log_dir, exist_ok=True)

        log_name = log_name if log_name else self.config.get('log_name_default', 'app')
        log_file = os.path.join(log_dir, f'{log_name}_{log_type}_{today}.log')

        file_handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=7, encoding='utf-8')
        file_handler.setLevel(log_level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        class LogQueueHandler(logging.Handler):
            def emit(self, record):
                log_entry = self.format(record)
                with log_lock:
                    # 及时丢弃旧日志
                    if log_queue.qsize() > MAX_LOG_QUEUE_SIZE:
                        log_queue.get()
                    log_queue.put(log_entry)  # 将日志消息放入队列

        queue_handler = LogQueueHandler()
        queue_handler.setLevel(log_level)

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
                    'pid': os.getpid(),
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

        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    'timestamp': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'ip': getattr(record, 'ip', ''),
                    'method': getattr(record, 'method', None),
                    'pid': os.getpid(),
                    'uuid': getattr(record, 'uuid', None),
                    'msg': getattr(record, 'msg', ''),
                    'data': getattr(record, 'data', None)
                }
                level_name = log_record['level']
                log_ext = '' if not log_record['method'] else f"[{log_record['method']}|{log_record['ip']}]"
                log_str = (f"[{log_record['timestamp']}] - {log_record['pid']} - {log_record['uuid'][-6:]} - {level_name} - "
                           f"{log_type}{log_ext} {log_record['msg']} - {log_record['data']}")[:768]

                if level_name in display_colors:
                    log_str = display_colors[level_name] + log_str + Logger.RESET
                return log_str

        formatter = JsonFormatter()
        console_formatter = formatter if self.display_json else ColoredFormatter()
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(console_formatter)
        queue_handler.setFormatter(console_formatter)

        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.addHandler(queue_handler)

        self._loggers[logger_key] = logger
        return logger

    def get_extra_data(self, data=None):
        if Http.is_http_request():
            # 尝试获取 HTTP 请求信息，如果能获取到说明是 HTTP 请求
            ip = Http.get_client_ip()
            route = request.path
            method = request.method
            headers = Http.get_request_headers()
            user_agent = Attr.get(headers, 'User-Agent')
            content_type = Attr.get(headers, 'Content-Type')
            authcode = Attr.get(headers, 'Authcode', '')
            request_params = dict(request.args)
            response = Attr.get(data, 'response')
            status_code = Attr.get(response, 'status_code', 100)
            response_result = Attr.get(response, 'response_result')
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
            command = "python " + " ".join(sys.argv if hasattr(sys, 'argv') else 'null')
            extra = {
                'uuid': self.uuid,
                'command': command,
                'data': data
            }
        return extra

    def get_log_queue(self):
        return self.log_queue

    @staticmethod
    def _make_serializable(data):
        """递归处理数据，确保所有内容都是JSON可序列化的"""
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data.hex()
        elif isinstance(data, dict):
            return {k: Logger._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Logger._make_serializable(item) for item in data]
        elif isinstance(data, (int, float, str, bool, type(None))):
            return data
        else:
            return str(data)

    def write(self, data=None, msg="", log_name="app", log_level='info'):
        # if log_level.lower() in ['error', 'critical']:
        #     # 发送告警消息
        #     client = 'utils.wechat.qywechat.qy_client.QyClient.send_error_msg'
        #     Transfer.middle_exec(client, [], err, logger.uuid)
        extra = self.get_extra_data(data)
        extra = Logger._make_serializable(extra)
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
        self.write(data, msg, log_name, 'critical')


