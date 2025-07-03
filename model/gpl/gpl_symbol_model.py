from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLSymbolModel(MysqlBaseModel):
    """
    股票基本信息表
        - id - int(11) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀，如SH600000)
        - code - varchar(8) - 股票代码(不带市场前缀，如600000)
        - market - varchar(10) - 交易所(SH/SZ/BJ)
        - org_name - varchar(128) - 公司简称
        - org_name_full - varchar(256) - 公司全称
        - org_name_hist - varchar(1024) - 公司曾用名
        - org_name_en - varchar(128) - 英文简称
        - org_name_en_full - varchar(256) - 英文全称
        - org_type - varchar(64) - 公司类型
        - org_description - text - 公司简介
        - main_business - text - 主营业务
        - main_business_full - text - 完整经营范围
        - industry_em - varchar(256) - 东财行业
        - industry_zjh - varchar(256) - 证监会行业
        - concept_list - text - 概念板块列表
        - reg_date - date - 注册日期
        - list_date - date - 上市日期
        - reg_asset - decimal(16,6) - 注册资本(百万元)
        - raise_money - decimal(16,6) - 实际募资净额(百万元)
        - issue_vol - decimal(16,6) - 发行数量(百万股)
        - issue_price - decimal(10,2) - 发行价格(元)
        - issue_money - decimal(16,6) - 发行总市值(百万元)
        - pe_rate - decimal(10,2) - 发行后市盈率
        - lottery_rate - decimal(10,4) - 网上发行中签率(%)
        - issue_way - varchar(64) - 发行方式
        - str_cxs - varchar(256) - 主承销商
        - str_bj - varchar(256) - 保荐机构
        - chairman - varchar(64) - 董事长
        - actual_managers - varchar(255) - 实际控股人列表
        - independent_directors - varchar(255) -        独立董事列表
        - manager_num - int(11) - 高管人数
        - general_manager - varchar(64) - 总经理
        - legal_representative - varchar(64) - 法定代表人
        - secretary - varchar(64) - 董事会秘书
        - staff_num - int(11) - 员工总数
        - gd_top10 - text - 十大股东列表
        - gd_top10_free - text - 十大流通股东列表
        - website - varchar(128) - 公司网站
        - reg_address - varchar(256) - 注册地址
        - office_address - varchar(256) - 办公地址
        - province - varchar(64) - 省份
        - city - varchar(64) - 城市
        - telephone - varchar(128) - 联系电话
        - fax - varchar(64) - 传真
        - postcode - varchar(32) - 邮编
        - email - varchar(128) - 邮箱
        - gs_code - varchar(64) - 工商登记号码
        - law_firm_name - varchar(256) - 律师事务所
        - account_firm_name - varchar(256) - 会计师事务所
        - trade_market - varchar(128) - 市场板块
        - market_type_name - varchar(128) - 市场类型
        - currency - varchar(128) - 币种
        - update_list - varchar(255) - 更新列表
        - remark - varchar(255) - 备注
        - extra - text - 额外参数
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_symbol'

    def add_symbol(self, data):
        """股票数据入库"""
        data = data if data else {}
        symbol = data.get('symbol', '')
        if not data or not symbol:
            return 0
        insert_data = {
            "symbol": symbol,
            "code": data.get('code', ''),
            "market": data.get('market', ''),
            "org_name": data.get('org_name', ''),
            "org_name_full": data.get('org_name_full', ''),
            "org_name_hist": data.get('org_name_hist', ''),
            "org_name_en": data.get('org_name_en', ''),
            "org_name_en_full": data.get('org_name_en_full', ''),
            "org_type": data.get('org_type', ''),
            "org_description": data.get('org_description', ''),
            "main_business": data.get('main_business', ''),
            "main_business_full": data.get('main_business_full', ''),
            "industry_em": data.get('industry_em', ''),
            "industry_zjh": data.get('industry_zjh', ''),
            "concept_list": data.get('concept_list', ''),
            "reg_date": data.get('reg_date', ''),
            "list_date": data.get('list_date', ''),
            "reg_asset": data.get('reg_asset', 0),
            "raise_money": data.get('raise_money', 0),
            "issue_vol": data.get('issue_vol', 0),
            "issue_price": data.get('issue_price', 0),
            "issue_money": data.get('issue_money', 0),
            "pe_rate": data.get('pe_rate', 0),
            "lottery_rate": data.get('lottery_rate', 0),
            "issue_way": data.get('issue_way', ''),
            "str_cxs": data.get('str_cxs', ''),
            "str_bj": data.get('str_bj', ''),
            "chairman": data.get('chairman', ''),
            "actual_managers": data.get('actual_managers', ''),
            "independent_directors": data.get('independent_directors', ''),
            "manager_num": data.get('manager_num', 0),
            "general_manager": data.get('general_manager', ''),
            "legal_representative": data.get('legal_representative', ''),
            "secretary": data.get('secretary', ''),
            "staff_num": data.get('staff_num', 0),
            "gd_top10": data.get('gd_top10', ''),
            "gd_top10_free": data.get('gd_top10_free', ''),
            "website": data.get('website', ''),
            "reg_address": data.get('reg_address', ''),
            "office_address": data.get('office_address', ''),
            "province": data.get('province', ''),
            "city": data.get('city', ''),
            "telephone": data.get('telephone', ''),
            "fax": data.get('fax', ''),
            "postcode": data.get('postcode', ''),
            "email": data.get('email', ''),
            "gs_code": data.get('gs_code', ''),
            "law_firm_name": data.get('law_firm_name', ''),
            "account_firm_name": data.get('account_firm_name', ''),
            "trade_market": data.get('trade_market', ''),
            "market_type_name": data.get('market_type_name', ''),
            "currency": data.get('currency', ''),
            "update_list": data.get('update_list', {}),
            "remark": Attr.get(data, 'remark', ''),
            "extra": Attr.get(data, 'extra', {})
        }
        return self.insert(insert_data)

    def update_symbol(self, symbol, data):
        """更新股票数据"""
        return self.update({'symbol': symbol}, data)

    def get_symbol_list(self, symbol_list):
        """获取股票数据列表"""
        return self.where_in('symbol', symbol_list).get()

    def get_symbol(self, symbol):
        """获取股票数据"""
        return self.where({'symbol': symbol}).first()
