import time
from datetime import datetime
from typing import Tuple, Union, Optional


class Time:

    @staticmethod
    def now(is_int=1):
        """
        获取当前时间戳
        :param is_int: 是否返回整数，默认是
        :return: 时间戳（整数，如 1744247999）
        """
        timestamp = datetime.now().timestamp()
        return int(timestamp) if is_int else timestamp

    @staticmethod
    def date(date_format="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期字符串
        :param date_format: 日期格式（如 "%Y-%m-%d %H:%M:%S"）
        :return: 默认格式 "YYYY-MM-DD HH:MM:SS"（如 "2025-04-10 09:19:59"）
        """
        return datetime.now().strftime(date_format)

    @staticmethod
    def sleep(f):
        """
        休眠一定时间
        :param f:  休眠时间 - 可以是整数或小数
        :return:
        """
        time.sleep(f)

    @staticmethod
    def tfd(date_str, date_format="%Y-%m-%d %H:%M:%S"):
        """
        将日期字符串转换为时间戳（秒级） - timestamp_from_date
        :param date_str: 日期字符串（如 "2025-04-10 09:19:59"）
        :param date_format: 日期格式（如 "%Y-%m-%d %H:%M:%S"）
        :return: 时间戳（整数，如 1744247999）
        """
        if not date_str:
            return 0
        try:
            dt = datetime.strptime(date_str, date_format)
            return int(dt.timestamp())
        except Exception as e:
            raise ValueError(f"日期格式无效[{date_str}]，应为 '{date_format}'。原始错误: {e}")

    @staticmethod
    def dft(timestamp, date_format="%Y-%m-%d %H:%M:%S"):
        """
        将时间戳转换为日期字符串 - date_from_timestamp
        :param timestamp: 秒级时间戳（如 1744247999）
        :param date_format: 日期格式（如 "%Y-%m-%d %H:%M:%S"）
        :return: 默认格式 "YYYY-MM-DD HH:MM:SS"（如 "2025-04-10 09:19:59"）
        """
        if not timestamp:
            timestamp = 0
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime(date_format)
        except Exception as e:
            raise ValueError(f"时间戳无效[{timestamp}]。原始错误: {e}")

    @staticmethod
    def month_last_day(date):
        """
        获取指定月的最后一天
        :param date:  日期 - Ym （如： 202503）
        :return: Ymd
        """
        n_date = Time.dft(Time.tfd(f'{date}28', '%Y%m%d') + 5 * 86400, '%Y%m01')
        return Time.dft(Time.tfd(n_date, '%Y%m%d') - 1, '%Y%m%d')

    @staticmethod
    def recent_season_day(n=0):
        """
        获取季度的最后一天
        :param n: 向前推几个季度
        :return: Ymd
        """
        date = Time.date()
        y = int(Time.dft(Time.tfd(date), '%Y'))
        m = int(Time.dft(Time.tfd(date), '%m'))
        for i in range(1, n + 2):
            if i > 1:
                m = int(m) - 3 if int(m) > 3 else 12
            if m <= 3:
                m = '03'
            elif m <= 6:
                m = '06'
            elif m <= 9:
                m = '09'
            else:
                m = '12'
                y -= 1
        n_date = f"{y}{m}"
        return Time.month_last_day(n_date)

    @staticmethod
    def start_end_time_list(
            params: Union[dict, str, None],
            return_type: str = "timestamp"
    ) -> Tuple[Optional[Union[int, str]], Optional[Union[int, str]]]:
        """
        根据params获取开始和结束时间
        :param params: 参数字典或字符串，包含时间参数
        :param return_type: 返回类型，timestamp(时间戳)或date(日期字符串)
        :return: (start_time, end_time) 出错返回 (None, None)
        
        ### 功能说明
            1. **参数处理**：
             - 自动识别 `dict`/`str`/`None` 输入
             - 支持多种时间键名 (`start_date`/`start_time`/`start_createtime` 及其 `end_` 变体)
             - 开始和结束时间都不存在 → 返回 `(None, None)`
             - 只有开始时间 → 结束时间补全为当前时间
             - 只有结束时间 → 开始时间补全为当天0点
             - 日期格式自动补全时分秒：
               - 开始时间 → `00:00:00`
               - 结束时间 → `23:59:59`
            2. **时间格式兼容**：
             - 时间戳：`1744289604` 或 `"1744289604"`
             - 日期格式：`20250101` 或 `2025-01-01`
             - 日期时间：`20250101123000` 或 `2025-01-01 12:30:00`
            3. **错误处理**：
             - 所有异常被静默处理
             - 无效输入返回 `(None, None)`
            4. **输出格式**：
             - `timestamp` 模式：返回整数时间戳
             - `date` 模式：返回 `"YYYY-MM-DD HH:MM:SS"` 字符串
            
        ### 使用示例
          params1 = {"start_date": "20250101", "end_createtime": "20250201"}
          params2 = {"start_time": 1744289604, "end_date": "2025-01-01"}
          params3 = "{'start_createtime':'20250101120000', 'end_time':'20250102130000'}"
          print(Time.start_end_time_list(params1))               # (1735660800, 1738252800 + 86399)
          print(Time.start_end_time_list(params2, "date"))   # ("2025-01-01 00:00:00", "2025-01-01 23:59:59")
          print(Time.start_end_time_list(params3, "date"))   # ("2025-01-01 12:00:00", "2025-01-02 13:00:00")
          print(Time.start_end_time_list(None))                   # (None, None)
          print(Time.start_end_time_list("invalid"))               # (None, None)
        """

        def _parse_time(time_val: Union[str, int, float]) -> Optional[datetime]:
            """静默解析各种时间格式"""
            try:
                # 处理空值
                if time_val is None:
                    return None

                # 处理时间戳（数字或字符串数字）
                if isinstance(time_val, (int, float)):
                    # 数字类型需要判断是否可能是日期格式（8位整数）
                    if 19000000 <= time_val <= 29999999:  # 合理的日期数字范围
                        return datetime.strptime(str(time_val), "%Y%m%d")
                    elif time_val > 1000000000:  # 时间戳
                        return datetime.fromtimestamp(time_val)
                    return None
                elif isinstance(time_val, str) and time_val.isdigit():
                    # 字符串数字需要判断长度
                    if len(time_val) == 8:  # 日期格式
                        return datetime.strptime(time_val, "%Y%m%d")
                    elif len(time_val) >= 10:  # 时间戳
                        timestamp = float(time_val)
                        if timestamp > 1000000000:
                            return datetime.fromtimestamp(timestamp)
                    return None

                # 处理字符串日期
                time_str = str(time_val).strip()
                time_str = time_str.replace("-", "").replace(" ", "").replace(":", "")

                if len(time_str) == 8:  # 纯日期格式 20250101
                    return datetime.strptime(time_str, "%Y%m%d")
                elif len(time_str) >= 14:  # 完整日期时间 20250101123000
                    return datetime.strptime(time_str[:14], "%Y%m%d%H%M%S")
                return None
            except:
                return None

        def _format_output(dt: Optional[datetime], is_end: bool = False) -> Optional[Union[int, str]]:
            """格式化输出结果"""
            if dt is None:
                return None

            # 处理未指定时分秒的情况
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                if is_end:
                    dt = dt.replace(hour=23, minute=59, second=59)

            if return_type == "date":
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return int(dt.timestamp())

        # 参数预处理
        if params is None:
            return None, None

        if not isinstance(params, dict):
            try:
                params = dict(params) if hasattr(params, "items") else eval(str(params))
            except:
                return None, None

        # 查找时间参数
        start_keys = ["start_date", "start_time", "start_createtime"]
        end_keys = [k.replace("start", "end") for k in start_keys]

        start_val = next((params.get(k) for k in start_keys if k in params), None)
        end_val = next((params.get(k) for k in end_keys if k in params), None)

        # 时间转换
        start_dt = _parse_time(start_val)
        end_dt = _parse_time(end_val)

        # 自动补全逻辑
        if start_dt is None and end_dt is None:
            return None, None
        elif start_dt is None and end_dt is not None:
            start_dt = end_dt.replace(hour=0, minute=0, second=0)
        elif start_dt is not None and end_dt is None:
            end_dt = datetime.now()

        # 格式化输出
        return (
            _format_output(start_dt),
            _format_output(end_dt, is_end=True)
        )








