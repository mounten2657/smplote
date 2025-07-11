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
        - f0_amplitude - decimal(12,2) - 不复权振幅
        - f0_pct_change - decimal(10,2) - 不复权涨跌幅(%)
        - f0_price_change - decimal(12,2) - 不复权涨跌额
        - f0_turnover_rate - decimal(10,2) - 不复权换手率(%)
        - f1_open - decimal(12,2) - 前复权开盘价
        - f1_close - decimal(12,2) - 前复权收盘价
        - f1_high - decimal(12,2) - 前复权最高价
        - f1_low - decimal(12,2) - 前复权最低价
        - f1_volume - bigint(20) - 前复权成交量(股)
        - f1_amount - decimal(20,2) - 前复权成交额(元)
        - f1_amplitude - decimal(12,2) - 前复权振幅
        - f1_pct_change - decimal(10,2) - 前复权涨跌幅(%)
        - f1_price_change - decimal(12,2) - 前复权涨跌额
        - f1_turnover_rate - decimal(10,2) - 前复权换手率(%)
        - f2_open - decimal(12,2) - 后复权开盘价
        - f2_close - decimal(12,2) - 后复权收盘价
        - f2_high - decimal(12,2) - 后复权最高价
        - f2_low - decimal(12,2) - 后复权最低价
        - f2_volume - bigint(20) - 后复权成交量(股)
        - f2_amount - decimal(20,2) - 后复权成交额(元)
        - f2_amplitude - decimal(12,2) - 后复权振幅
        - f2_pct_change - decimal(10,2) - 后复权涨跌幅(%)
        - f2_price_change - decimal(12,2) - 后复权涨跌额
        - f2_turnover_rate - decimal(10,2) - 后复权换手率(%)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_daily'

    def add_daily(self, data_list):
        """股票日线数据入库"""
        insert_list = []
        data_list = data_list if data_list else []
        if not data_list:
            return 0
        for data in data_list:
            insert_list.append({
                "symbol": data.get('symbol', ''),
                "trade_date": data.get('trade_date', ''),
                "f0_open": data.get('f0_open', 0),
                "f0_close": data.get('f0_close', 0),
                "f0_high": data.get('f0_high', 0),
                "f0_low": data.get('f0_low', 0),
                "f0_volume": data.get('f0_volume', 0),
                "f0_amount": data.get('f0_amount', 0),
                "f0_amplitude": data.get('f0_amplitude', 0),
                "f0_pct_change": data.get('f0_pct_change', 0),
                "f0_price_change": data.get('f0_price_change', 0),
                "f0_turnover_rate": data.get('f0_turnover_rate', 0),
                "f1_open": data.get('f1_open', 0),
                "f1_close": data.get('f1_close', 0),
                "f1_high": data.get('f1_high', 0),
                "f1_low": data.get('f1_low', 0),
                "f1_volume": data.get('f1_volume', 0),
                "f1_amount": data.get('f1_amount', 0),
                "f1_amplitude": data.get('f1_amplitude', 0),
                "f1_pct_change": data.get('f1_pct_change', 0),
                "f1_price_change": data.get('f1_price_change', 0),
                "f1_turnover_rate": data.get('f1_turnover_rate', 0),
                "f2_open": data.get('f2_open', 0),
                "f2_close": data.get('f2_close', 0),
                "f2_high": data.get('f2_high', 0),
                "f2_low": data.get('f2_low', 0),
                "f2_volume": data.get('f2_volume', 0),
                "f2_amount": data.get('f2_amount', 0),
                "f2_amplitude": data.get('f2_amplitude', 0),
                "f2_pct_change": data.get('f2_pct_change', 0),
                "f2_price_change": data.get('f2_price_change', 0),
                "f2_turnover_rate": data.get('f2_turnover_rate', 0),
            })
        return self.insert(insert_list)

    def update_daily(self, pid, data):
        """更新股票日线数据"""
        return self.update({'id': pid}, data)

    def get_daily_list(self, symbol_list, trade_date_list):
        """获取股票日线数据列表"""
        where = {
            'symbol': {'opt': 'in', 'val': symbol_list},
            'trade_date': {'opt': 'between', 'val': trade_date_list},
        }
        return self.where(where).get()

    def get_daily(self, symbol, trade_date):
        """获取股票日线数据"""
        if isinstance(trade_date, list):
            return self.where_in('trade_date', trade_date).where({'symbol': symbol}).get()
        else:
            return self.where({'symbol': symbol, 'trade_date': trade_date}).first()
