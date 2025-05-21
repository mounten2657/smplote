import argparse
import importlib
from tool.core import Logger, Time, Http, Error, Attr
from utils.wechat.qywechat.qy_client import QyClient
from gevent import monkey

monkey.patch_all(ssl=False)
logger = Logger()


class ParseHandler:
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
            # 发送告警消息
            QyClient().send_error_msg(err, logger.uuid)
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