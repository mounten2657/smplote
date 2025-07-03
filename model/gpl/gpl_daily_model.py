from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLDailyModel(MysqlBaseModel):
    """
    股票日线行情表 - 已按年分区
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - trade_date - date - 交易日期
        - f0_open - decimal(12,2) - 不复权开盘价
        - f0_close - decimal(12,2) - 不复权收盘价
        - f0_high - decimal(12,2) - 不复权最高价
        - f0_low - decimal(12,2) - 不复权最低价
        - f0_volume - bigint(20) - 不复权成交量(股)
        - f0_amount - decimal(20,2) - 不复权成交额(元)
        - f0_amplitude - decimal(12,2) - 不复权涨跌额
        - f0_pct_chg - decimal(10,2) - 不复权涨跌幅(%)
        - f0_price_change - decimal(12,2) - 不复权涨跌额
        - f0_turnover_rate - decimal(10,2) - 不复权换手率(%)
        - f1_open - decimal(12,2) - 前复权开盘价
        - f1_close - decimal(12,2) - 前复权收盘价
        - f1_high - decimal(12,2) - 前复权最高价
        - f1_low - decimal(12,2) - 前复权最低价
        - f1_volume - bigint(20) - 前复权成交量(股)
        - f1_amount - decimal(20,2) - 前复权成交额(元)
        - f1_amplitude - decimal(12,2) - 前复权涨跌额
        - f1_pct_chg - decimal(10,2) - 前复权涨跌幅(%)
        - f1_price_change - decimal(12,2) - 前复权涨跌额
        - f1_turnover_rate - decimal(10,2) - 前复权换手率(%)
        - f2_open - decimal(12,2) - 后复权开盘价
        - f2_close - decimal(12,2) - 后复权收盘价
        - f2_high - decimal(12,2) - 后复权最高价
        - f2_low - decimal(12,2) - 后复权最低价
        - f2_volume - bigint(20) - 后复权成交量(股)
        - f2_amount - decimal(20,2) - 后复权成交额(元)
        - f2_amplitude - decimal(12,2) - 后复权涨跌额
        - f2_pct_chg - decimal(10,2) - 后复权涨跌幅(%)
        - f2_price_change - decimal(12,2) - 后复权涨跌额
        - f2_turnover_rate - decimal(10,2) - 后复权换手率(%)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_daily'

    def add_daily(self, data):
        """股票数据入库"""
        data = data if data else {}
        symbol = data.get('symbol', '')
        if not data or not symbol:
            return 0
        insert_data = {
            "symbol": data.get('symbol', ''),
            "trade_date": data.get('trade_date', ''),
            "f0_open": data.get('f0_open', ''),
            "f0_close": data.get('f0_close', ''),
            "f0_high": data.get('f0_high', ''),
            "f0_low": data.get('f0_low', ''),
            "f0_volume": data.get('f0_volume', ''),
            "f0_amount": data.get('f0_amount', ''),
            "f0_amplitude": data.get('f0_amplitude', ''),
            "f0_pct_chg": data.get('f0_pct_chg', ''),
            "f0_price_change": data.get('f0_price_change', ''),
            "f0_turnover_rate": data.get('f0_turnover_rate', ''),
        }
        return self.insert(insert_data)

    def update_daily(self, pid, data):
        """更新股票数据"""
        return self.update({'id': pid}, data)

    def get_daily(self, symbol, trade_date):
        """获取股票数据"""
        if isinstance(trade_date, list):
            return self.where_in('trade_date', trade_date).where({'symbol': symbol}).get()
        else:
            return self.where({'symbol': symbol, 'trade_date': trade_date}).first()
