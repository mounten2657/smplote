import baostock as bs
from tool.core import Logger, Error, Str, Attr, Time

logger = Logger()


class BsDataSource:
    """
    baostock数据源

    api_doc: http://www.baostock.com/mainContent?file=home.md
    """

    DATA_TYPE = 'dict'

    def __init__(self, data_type=DATA_TYPE):
        self.data_type = data_type

    @staticmethod
    def _bs_formatter(func):
        """数据格式化返回装饰器"""
        def wrapper(*args, **kwargs):
            function_name = func.__name__
            all_args = list(args) + [f"{k}={v}" for k, v in kwargs.items()]
            all_args.pop(0)
            try:
                res = func(*args, **kwargs)
                if isinstance(res, dict) or isinstance(res, list):
                    return res
                if 'dict' == BsDataSource.DATA_TYPE:
                    res = res.to_dict('records')
                return res
            except Exception as e:
                err = Error.handle_exception_info(e)
                err['ext'] = {"func": function_name, "args": all_args, "msg": "请求BS接口失败"}
                logger.warning(err, 'BS_API_ERR')
                return []
        return wrapper

    def get_daily_quote_bs(self, stock_code: str, sd: str = "2000-01-01", ed: str = "2099-01-01", adjust: str = "", period: str = "daily"):
        """
        获取股票日线行情 - BS

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 开始日期 - Ymd 或 Y-m-d（如： 2025-03-01）
        :param str ed: 结束日期 - Ymd 或 Y-m-d（如： 2025-03-02）
        :param str adjust: key of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
        :param str period: key of {"daily": "d", "weekly": "w", "monthly": "m"}
        :return: 日线行情数据列表，每个元素为一个交易日数据字典
        [{'date': '2025-06-27', 'open': 7.13, 'close': 7.19, 'high': 7.19, 'low': 7.06, 'volume': 41573, 'amount': 29676241.0, 'amplitude': 1.83, 'pct_change': 1.13, 'price_change': 0.08, 'turnover_rate': 1.97}]
        """
        rl = []
        # bs.login()  # 无需账户，直接登录成功
        # 自动转换日期格式
        sd = Time.dfd(sd, '%Y-%m-%d')
        ed = Time.dfd(ed, '%Y-%m-%d')
        # volume 成交量单位是股 | amount 成交额单位是元 | pctChg 涨跌幅 | turn 换手率 | preclose 昨收价
        fields = "date,code,open,close,high,low,volume,amount,pctChg,turn,preclose"
        adjust_dict = {"hfq": "1", "qfq": "2", "": "3"}  # 1=后复权，2=前复权，3=不复权
        period_dict = {"daily": "d", "weekly": "w", "monthly": "m"}
        # 请求BS接口
        prefix = Str.get_stock_prefix(stock_code)
        code = f"{prefix}.{stock_code}".lower()
        rs = bs.query_history_k_data_plus(
            code, fields, start_date=sd, end_date=ed,
            frequency=period_dict[period], adjustflag=adjust_dict[adjust]
        )
        rst = rs.get_data()
        if not rst:
            return []
        rst = rst.to_dict('records')
        if rst:
            for i, rt in enumerate(rst):
                rt['volume'] = round(float(rt['volume']) / 100, 2)  # 成交量单位换成手，100股 = 1手
                rt['amplitude'] = round((float(rt['high']) - float(rt['low'])) / float(rt['preclose']) * 100, 2)  # 振幅 = (high - low)/preclose * 100
                rt['pct_change'] = float(rt['pctChg'])  # 涨跌幅 = (close - preclose)/preclose * 100
                rt['price_change'] = round(float(rt['close']) - float(rt['preclose']), 2) # 涨跌额 = close - preclose
                rt['turnover_rate'] = float(rt['turn']) # 换手率，保留两位小数
                # 统一保留两位小数，字符串形式
                rst[i] = {k: str(Str.round(v, 2)) if Str.is_float(v) else v for k, v in rt.items()}
                # 移除不必要的键，保持数据格式的统一
                rst[i] = Attr.remove_keys(rst[i], ['pctChg', 'turn', 'preclose', 'code'])
            rl.extend(rst)
        # bs.logout()  # 用完即退
        return rl

