import sys
import traceback
from tool.core.attr import Attr
from tool.core.env import Env


class Error:
    @staticmethod
    def handle_exception_info(e):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # 异常参数
        exception_args = e.args
        # 当前异常名
        current_exception_name = exc_type.__name__
        # 原始异常名，如果没有原始异常则为 None
        original_exception_name = e.__cause__.__class__.__name__ if e.__cause__ else None

        # 异常发生的文件和行数的列表，用冒号连接文件名和行号
        file_line_list = []
        tb = exc_traceback
        while tb:
            frame_summary = traceback.extract_tb(tb, limit=1)[0]
            # 过滤前面的绝对路径，只保留项目的相对路径
            app_name = Env.get('APP_NAME', 'smplote')
            if app_name not in frame_summary.filename:
                app_name = 'envs'
            if '<frozen' in frame_summary.filename:
                file_name = frame_summary.filename
            else:
                file_name = frame_summary.filename.split(app_name)
                file_name = (file_name[1] if len(file_name) > 1 else file_name[0]).replace('\\', '/')[1:]
            file_line = f"{file_name}:{frame_summary.lineno}"
            file_line_list.append(file_line)
            tb = tb.tb_next

        result = {
            "err_msg": exception_args,
            "err_cause": [current_exception_name, original_exception_name],
            "err_file_list": file_line_list
        }
        return result

    @staticmethod
    def has_exception(data):
        return Attr.has_keys(data, ['err_msg', 'err_cause'])

    @staticmethod
    def has_error(data):
        return Attr.has_keys(data, ['code', 'msg', 'data']) and data['code']

    @staticmethod
    def throw_exception(msg, code=None):
        """抛出异常 - 适用于不方便 return 的场景"""
        raise Exception(msg, code)
