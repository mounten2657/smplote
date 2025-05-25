import os
import argparse
import importlib
import signal
import logging
import time
from tool.core import Logger, Time, Http, Error, Attr, Config
from tool.db.cache.redis_client import RedisClient
from tool.db.cache.redis_task_queue import RedisTaskQueue
from utils.wechat.qywechat.qy_client import QyClient
from utils.wechat.vpwechat.vp_client import VpClient

logger = Logger()


class ParseHandler:

    @staticmethod
    def init_program():
        """初始化程序"""
        res = {}
        # 注册结束处理
        signal.signal(signal.SIGINT, ParseHandler.shutdown_handler)
        # 程序开始前先释放锁
        key_list = ['LOCK_RTQ_CNS', 'LOCK_SQL_CNT', 'LOCK_WSS_CNT']
        list(map(lambda key: RedisClient().delete(key), key_list))
        app_config = Config.app_config()
        # 程序预热
        if int(app_config['APP_AUTO_START_WS']):
            res['ws_start'] = VpClient().start_websocket()           # 启动 wechatpad ws
        res['que_start'] = RedisTaskQueue().run_consumer()   # 启动 redis task queue
        return res

    @staticmethod
    def shutdown_handler(signum, frame):
        """优雅退出"""
        pid = os.getpid()
        print(f"PID[{pid}]: 正在清理资源，请稍候...")
        # 清理日志资源
        logging.shutdown()
        # 清理vp资源
        if Config.is_prod():
            VpClient().close_websocket(is_all=1)
            # 等待资源释放完毕
            time.sleep(3)
        print(f"PID[{pid}]: 清理完成，主程序结束")
        exit(0)

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='微信工具集，提供各种个人微信号的玩法')
        parser.add_argument('-m', '--method', type=str,
                            help='方法路径：格式为 module.control.method，用于指定要执行的方法所在的模块和方法名')
        parser.add_argument('-p', '--params', type=str, default='',
                            help='额外参数：格式为 "key1=value1&key2=value2"，用于传递给目标方法的额外参数')
        return parser.parse_args()

    @staticmethod
    def parse_params(param_str):
        params = {}
        if Attr.get(param_str, 'params'):
            pairs = param_str.params.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    params[key] = value
        return params

    @staticmethod
    def execute_method(path, params):
        start_time = Time.now(0)
        try:
            not Http.is_http_request() and logger.info(data={"path": path, "params": params}, msg=f"START[RT.{int(start_time)}]")
            # 分割路径为模块路径和方法名
            module_path, method_name = path.rsplit('.', 1)
            # 将模块名转换为大驼峰形式的类名
            class_name_parts = module_path.split('.')[-1].split('_')
            class_name = ''.join(part.capitalize() for part in class_name_parts)
            # 动态导入模块
            module = importlib.import_module(f'app.{module_path}')
            # 获取类
            class_obj = getattr(module, class_name)
            instance = class_obj()
            # 获取方法对象
            method = getattr(instance, method_name)
            # 执行方法
            result = method()
            run_time = Time.now(0) - start_time
            not Http.is_http_request() and logger.info(data=Attr.parse_json_ignore(result), msg=f"END[RT.{run_time}]")
            return result
        except (ImportError, AttributeError, RuntimeError, Exception) as e:
            run_time = Time.now(0) - start_time
            err = Error.handle_exception_info(e)
            logger.error(data=err, msg=f"ERROR[RT.{run_time}]")
            QyClient().send_error_msg(err, logger.uuid)  # 发送告警消息
            return err

    @staticmethod
    def get_command_method():
        args = ParseHandler.parse_args()
        return Attr.get(args, 'method')

    @staticmethod
    def get_method_name():
        """获取当前请求的接口方法名"""
        module, method_name = ParseHandler.get_command_method().rsplit('.', 1)
        return method_name

    @staticmethod
    def get_command_params():
        return ParseHandler.parse_params(ParseHandler.parse_args())

    def run_app(self):
        return self.execute_method(self.get_command_method(), self.get_command_params())