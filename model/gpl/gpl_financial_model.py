from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLFinancialModel(MysqlBaseModel):
    """
    股票财务指标表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - report_date - date - 报告期(季度末/年度末)
        - report_type - varchar(10) - 报告类型(Q1/Q2/Q3/Annual)
        - eps - decimal(12,4) - 每股收益(元)
        - bps - decimal(12,4) - 每股净资产(元)
        - roe - decimal(10,4) - 净资产收益率(%)
        - gross_profit_margin - decimal(10,4) - 销售毛利率(%)
        - net_profit_margin - decimal(10,4) - 销售净利率(%)
        - total_revenue - decimal(20,4) - 营业总收入(元)
        - revenue_yoy - decimal(10,4) - 营业收入同比增长(%)
        - net_profit - decimal(20,4) - 净利润(元)
        - net_profit_yoy - decimal(10,4) - 净利润同比增长(%)
        - total_assets - decimal(20,4) - 总资产(元)
        - total_liabilities - decimal(20,4) - 总负债(元)
        - debt_to_equity - decimal(10,4) - 资产负债率(%)
        - operating_cash_flow - decimal(20,4) - 经营活动现金流量净额(元)
        - investing_cash_flow - decimal(20,4) - 投资活动现金流量净额(元)
        - financing_cash_flow - decimal(20,4) - 筹资活动现金流量净额(元)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_financial'

    def add_financial(self, data):
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

    def update_financial(self, pid, data):
        """更新股票数据"""
        return self.update({'id': pid}, data)

    def get_financial(self, symbol):
        """获取股票数据"""
        return self.where({'symbol': symbol}).first()
