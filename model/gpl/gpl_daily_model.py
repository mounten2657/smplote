from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLDailyModel(MysqlBaseModel):
    """
    股票日线行情表 - 已按年分区
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - trade_date - date - 交易日期
        - open - decimal(12,4) - 开盘价
        - high - decimal(12,4) - 最高价
        - low - decimal(12,4) - 最低价
        - close - decimal(12,4) - 收盘价
        - pre_close - decimal(12,4) - 前收盘价
        - volume - bigint(20) - 成交量(股)
        - amount - decimal(20,4) - 成交额(元)
        - change - decimal(12,4) - 涨跌额
        - pct_chg - decimal(10,4) - 涨跌幅(%)
        - turnover_rate - decimal(10,4) - 换手率(%)
        - pe_ttm - decimal(12,4) - 滚动市盈率
        - pb - decimal(12,4) - 市净率
        - ps_ttm - decimal(12,4) - 滚动市销率
        - pcf_ttm - decimal(12,4) - 滚动市现率
        - extra - text - 额外参数
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
            "code": data.get('code', ''),
        }
        return self.insert(insert_data)

    def update_daily(self, pid, data):
        """更新股票数据"""
        return self.update({'id': pid}, data)

    def get_daily(self, symbol, trade_date):
        """获取股票数据"""
        return self.where({'symbol': symbol, 'trade_date': trade_date}).first()
