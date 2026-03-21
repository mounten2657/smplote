import os
import re
import json
import logging
from flask import request
from queue import Queue
from threading import Lock
from datetime import datetime
from tool.core.config import Config
from tool.core.dir import Dir
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
            # cls._instance.__init__()  # new 执行完后会自动调用 init
        return cls._instance

    def __init__(self):
        self.root_dir = Dir.root_dir()
        self.config = Config.logger_config()
        self.log_level = self.config.get('log_level', 'DEBUG')
        self.log_path = self.config.get('log_path', 'storage/logs')
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
        log_dir = f"{self.root_dir}/{self.log_path}/{today}"
        os.makedirs(log_dir, exist_ok=True)

        log_name = log_name if log_name else self.config.get('log_name_default', 'app')
        log_file = f'{log_dir}/{log_name}_{log_type}_{today}.log'

        # 使用普通 Handler
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
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
            def format(self, record):
                # 完整日志结构
                log_record = {
                    'time': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'pid': os.getpid(),
                    'uuid': getattr(record, 'uuid', ''),
                    'type': getattr(record, 'type', ''),
                    'msg': getattr(record, 'msg', ''),
                    'sys': getattr(record, 'sys', ''),
                    'data': getattr(record, 'data', '')
                }
                return json.dumps(log_record, ensure_ascii=False)

        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                # 终端输出结构
                console = {
                    'time': self.formatTime(record, '%Y-%m-%d %H:%M:%S'),
                    'level': record.levelname,
                    'pid': os.getpid(),
                    'uuid': getattr(record, 'uuid', ''),
                    'type': getattr(record, 'type', ''),
                    'msg': getattr(record, 'msg', ''),
                    'data': getattr(record, 'data', '')
                }
                level_name = console['level']
                sys = Attr.parse_json_ignore(getattr(record, 'sys', ''))
                log_ext = f"[{sys['method']}|{sys['ip']}]" if Attr.get(sys, 'ip') else ""
                log_str = (f"[{console['time']}] - {console['pid']} - {console['uuid'][-6:]} - {level_name} - "
                           f"{console['type']}{log_ext} - {console['msg']} - {console['data']}")[:768]
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

    def get_extra_data(self, data, msg, log_type):
        """日志原始数据组装"""
        sys = {}
        # 解析 msg - "{msg}[RT.{run_time}]@{uuid}"
        msg, run_time, uuid = self._extract_msg(msg)
        if log_type == 'http':
            method = request.method
            route = request.path
            ip = Http.get_client_ip()
            headers = Http.get_request_headers()
            user_agent = Attr.get(headers, 'User-Agent', '')
            # content_type = Attr.get(headers, 'Content-Type', '')
            # authcode = Attr.get(headers, 'Authcode', '')
            request_params = dict(request.args)
            response = Attr.get(data, 'response')
            status_code = Attr.get(response, 'status_code', 100)
            data = Attr.get(response, 'response_result', {})  # 重塑data，避免重复记录
            sys = {
                'method': method,
                'route': route,
                'status_code': status_code,
                'ip': ip,
                'user_agent': user_agent,
                # 'content_type': content_type,
                # 'authcode': authcode,
                'request_params': request_params
            }
        sys['run_time'] = float(run_time)
        return {
            'uuid': self.uuid if not uuid else uuid,
            'type': log_type,
            'msg': msg,
            'sys': sys,
            'data': data
        }

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

    @staticmethod
    def _extract_msg(log_str: str) -> tuple:
        """
        从指定格式的日志字符串中提取 msg、run_time、uuid

        :param log_str: 日志字符串，格式如 "END[RT.12.34]@d34c33"
        :return: 提取结果 - 元组
        """
        # 正则解析：匹配 [RT.xxx]@xxx 格式，精准分组提取
        pattern = r'^(?P<msg>.+)\[RT\.(?P<run_time>[\d\.]+)\]@(?P<uuid>.+)$'
        match = re.match(pattern, log_str.strip())
        if match:
            uuid = match.group('uuid')
            uuid = uuid if len(uuid) > 1 else ''
            return match.group('msg'), match.group('run_time'), uuid
        return log_str, 0, ''

    def write(self, data=None, msg="", log_name="app", log_level='info'):
        log_type = 'http' if Http.is_http_request() else 'cmd'  # 区分 Http请求 和 后台运行
        extra = self.get_extra_data(data, msg, log_type)
        extra = Logger._make_serializable(extra)
        msg = extra.pop('msg')  # 这里必须弹出，否则会与 logging 内部的变量名冲突
        logger_handle = self.setup_logger(log_type, log_name)
        method = getattr(logger_handle, log_level.lower())
        method(msg, extra=extra)
        # 发送告警消息
        if log_level.lower() in ['error', 'critical']:
            err = {
                "err_msg": [msg, str(data)],
                "err_cause": ["execute_exception", "None"],
                "err_file_list": [f"{log_name}:{log_level}"]
            }
            data_str = str(data)
            if isinstance(data, dict) and data.get('err_cause'):
                err = data
            elif ' - {' in data_str:
                d_msg, d_str = data_str.rsplit(' - ', 1)
                d_json = Attr.parse_json_ignore(str(d_str).strip())
                if d_json and isinstance(d_json, dict) and d_json.get('err_msg'):
                    d_json['err_msg'].insert(0, d_msg)
                    err = d_json
            client = 'utils.wechat.qywechat.qy_client.QyClient.send_error_msg'
            Transfer.middle_exec(client, [], err, self.uuid)

    def debug(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'debug')

    def info(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'info')

    def warning(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'warning')

    def error(self, data=None, msg="NULL", log_name="app"):
        self.write(data, msg, log_name, 'error')

    def exception(self, data=None, msg="NULL", log_name="app"):
        # self.write(data, msg, log_name, 'critical')
        self.write(data, msg, log_name, 'error')
