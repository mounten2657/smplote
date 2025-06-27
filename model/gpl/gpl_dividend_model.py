from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLDividendModel(MysqlBaseModel):
    """
    股票分红送配表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - announce_date - date - 公告日期
        - ex_dividend_date - date - 除权除息日
        - dividend_payment_date - date - 派息日
        - dividend - decimal(10,4) - 每股派息(元)
        - bonus_share_ratio - decimal(10,4) - 每股送股比例(10送X)
        - conversion_ratio - decimal(10,4) - 每股转增比例(10转增X)
        - dividend_yield - decimal(10,4) - 股息率(%)
        - equity_record_date - date - 股权登记日
        - plan_progress - varchar(50) - 方案进度(预案/股东大会通过/实施)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_dividend'

    def add_dividend(self, data):
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

    def update_dividend(self, pid, data):
        """更新股票数据"""
        return self.update({'id': pid}, data)

    def get_dividend(self, symbol):
        """获取股票数据"""
        return self.where({'symbol': symbol}).first()

