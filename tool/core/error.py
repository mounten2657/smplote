import sys
import traceback
from tool.core.attr import Attr


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
            file_line = f"{frame_summary.filename}:{frame_summary.lineno}"
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
