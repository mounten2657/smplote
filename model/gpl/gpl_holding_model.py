from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLHoldingModel(MysqlBaseModel):
    """
    股票机构持股表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - report_date - date - 报告日期
        - institution_type - varchar(50) - 机构类型(基金/社保/QFII等)
        - holding_count - int(11) - 持有机构家数
        - total_shares - decimal(20,4) - 持股总数(股)
        - total_shares_percent - decimal(10,4) - 占总股本比例(%)
        - total_market_value - decimal(20,4) - 持股市值(元)
        - change_shares - decimal(20,4) - 持股变化(股)
        - change_percent - decimal(10,4) - 持股变化比例(%)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_holding'

    def add_holding(self, data):
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

    def update_holding(self, pid, data):
        """更新股票数据"""
        return self.update({'id': pid}, data)

    def get_holding(self, symbol):
        """获取股票数据"""
        return self.where({'symbol': symbol}).first()
