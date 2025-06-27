from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLFlowModel(MysqlBaseModel):
    """
    股票资金流向表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - trade_date - date - 交易日期
        - main_net_inflow - decimal(20,4) - 主力净流入(元)
        - main_net_inflow_rate - decimal(10,4) - 主力净占比(%)
        - large_net_inflow - decimal(20,4) - 超大单净流入(元)
        - large_net_inflow_rate - decimal(10,4) - 超大单净占比(%)
        - medium_net_inflow - decimal(20,4) - 大单净流入(元)
        - medium_net_inflow_rate - decimal(10,4) - 大单净占比(%)
        - small_net_inflow - decimal(20,4) - 小单净流入(元)
        - small_net_inflow_rate - decimal(10,4) - 小单净占比(%)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_flow'

    def add_flow(self, data):
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

    def update_flow(self, pid, data):
        """更新股票数据"""
        return self.update({'id': pid}, data)

    def get_flow(self, symbol):
        """获取股票数据"""
        return self.where({'symbol': symbol}).first()
