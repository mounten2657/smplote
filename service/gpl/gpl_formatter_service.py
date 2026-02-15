from model.gpl.gpl_symbol_model import GPLSymbolModel
from utils.gpl.source.ak_data_source import AkDataSource
from utils.gpl.source.bs_data_source import BsDataSource
from utils.gpl.source.em_data_sub_source import EmDataSubSource
from utils.gpl.formatter.stock_str_formatter import StockStrFormatterService
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


class GplFormatterService:
    """股票获取类"""

    # 初始化的开始结束日期
    INIT_ST = '2000-01-01'
    INIT_ET = '2025-09-30'

    def __init__(self):
        self.ak = AkDataSource()
        self.bs = BsDataSource()
        self.em = EmDataSubSource()
        self.sft = StockStrFormatterService()
        self.sdb = GPLSymbolModel()

    def get_stock(self, code):
        """从数据库中获取股票信息"""
        code = self.sft.remove_stock_prefix(code)
        symbol = self.sft.add_stock_prefix(code)
        return self.sdb.get_symbol(symbol)

    def get_stock_info(self, code, is_merge=0):
        """
        获取股票数据 - 有缓存 - 雪球 <-- 东财
        :param code: 股票代码，不带市场前缀，如 603777
        :param is_merge: 是否多来源合并，默认否
        :return: 标准股票数据
        """
        if not code:
            return {}
        em = self.get_stock_em(code)
        stock_info = em
        if is_merge:
            xq = self.get_stock_xq(code)
            stock_info = Attr.merge_dicts_soft(xq, em)
        if not stock_info.get('org_name'):
            return {}
        return stock_info

    @Ins.cached('GPL_STOCK_CODE_LIST')
    def get_stock_code_all(self):
        """
        获取所有股票代码列表 - 不含市场标识 - 约 5423 只
        :return: 股票代码列表 - 不带前缀 - ["123456", ...]
        """
        code_list = self.ak.stock_info_a_code_name()
        code_list = [str(item['code']) for item in code_list]
        db_list = self.sdb.get_code_list_all()
        return sorted(list(dict.fromkeys(code_list + db_list)))

    @Ins.cached('GPL_STOCK_TD_LIST')
    def get_trade_day_all(self):
        """
        获取所有有效的交易日期 - 待优化，这里只是个大概
        :return: 股票有效交易日期
        """
        p_list = self.em.get_daily_quote('000001', '2000-01-01', Time.date('%Y-%m-%d'))
        return [p['date'] for p in p_list]

    @Ins.cached('GPL_STOCK_INFO_EM')
    def get_stock_em(self, code):
        """
        获取东财股票数据
        数据来源 - https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=SZ300126&color=b#/gsgk
        :param code: 股票代码，不带市场前缀，如 603777
        :return: 标准股票数据
        """
        code = self.sft.remove_stock_prefix(code)
        symbol = self.sft.add_stock_prefix(code)
        try:
            stock = self.em.get_basic_info(symbol)
            issue = self.em.get_issue_info(symbol)
            if not stock.get('SECURITY_NAME_ABBR') or not issue.get('FOUND_DATE'):
                logger.warning(f"获取股票数据失败[EM]<{symbol}> - {stock}", 'GET_STOCK_WAR')
                return {}
            market = Str.replace_multiple(symbol, [code, '.'])
            province, city = self.sft.extract_province_city(Attr.get(stock, 'ADDRESS', ''))
            default_date = '1970-01-01 00:00:00'
            reg_date = Attr.get(stock, 'FOUND_DATE', default_date)[:10]
            list_date = Attr.get(stock, 'LISTING_DATE', default_date)[:10]
            stock_info = {
                "symbol": symbol,
                "code": code,
                "market": market,
                "org_name": Attr.get(stock, 'SECURITY_NAME_ABBR', ''),
                "org_name_full": Attr.get(stock, 'ORG_NAME', ''),
                "org_name_hist": Attr.get(stock, 'FORMERNAME', ''),
                "org_name_en_full": Attr.get(stock, 'ORG_NAME_EN', ''),
                "org_description": Attr.get(stock, 'ORG_PROFILE', '').strip(),
                "main_business": Attr.get(stock, 'MAIN_BUSINESS', '').strip(),
                "main_business_full": Attr.get(stock, 'BUSINESS_SCOPE', '').strip(),
                "industry_em": Attr.get(stock, 'EM2016', ''),
                "industry_zjh": Attr.get(stock, 'INDUSTRYCSRC1', ''),
                "reg_date": reg_date,
                "list_date": list_date,
                "reg_asset": round(Attr.get(stock, 'REG_CAPITAL', 0.0) / 100, 6),
                "raise_money": round(Attr.get(issue, 'NET_RAISE_FUNDS', 0.0) / 1000000, 6),
                "issue_vol": round(Attr.get(issue, 'TOTAL_ISSUE_NUM', 0.0) / 1000000, 6),
                "issue_price": round(Attr.get(issue, 'ISSUE_PRICE', 0.0), 2),
                "issue_money": round(Attr.get(issue, 'TOTAL_FUNDS', 0.0) / 1000000, 6),
                "pe_rate": round(Attr.get(issue, 'AFTER_ISSUE_PE', 0.0), 2),
                "lottery_rate": round(Attr.get(issue, 'ONLINE_ISSUE_LWR', 0.0), 4),
                "issue_way": Attr.get(stock, 'ISSUE_WAY', ''),
                "str_cxs": Attr.get(stock, 'STR_ZHUCHENGXIAO', ''),
                "str_bj": Attr.get(stock, 'STR_BAOJIAN', ''),
                "chairman": Attr.get(stock, 'CHAIRMAN', ''),
                "actual_managers": Attr.get(stock, 'ACTUAL_HOLDER', ''),
                "independent_directors": Attr.get(stock, 'INDEDIRECTORS', ''),
                "manager_num": Attr.get(stock, 'TATOLNUMBER', ''),
                "general_manager": Attr.get(stock, 'PRESIDENT', ''),
                "legal_representative": Attr.get(stock, 'LEGAL_PERSON', ''),
                "secretary": Attr.get(stock, 'SECRETARY', ''),
                "staff_num": Attr.get(stock, 'EMP_NUM', 0),
                "website": Attr.get(stock, 'ORG_WEB', ''),
                "reg_address": Attr.get(stock, 'REG_ADDRESS', ''),
                "office_address": Attr.get(stock, 'ADDRESS', ''),
                "province": province,
                "city": city,
                "telephone": Attr.get(stock, 'ORG_TEL', ''),
                "fax": Attr.get(stock, 'ORG_FAX', ''),
                "postcode": Attr.get(stock, 'ADDRESS_POSTCODE', ''),
                "email": Attr.get(stock, 'ORG_EMAIL', ''),
                "gs_code": Attr.get(stock, 'REG_NUM', ''),
                "law_firm_name": Attr.get(stock, 'LAW_FIRM', ''),
                "account_firm_name": Attr.get(stock, 'ACCOUNTFIRM_NAME', ''),
                "trade_market": Attr.get(stock, 'TRADE_MARKETT', ''),
                "market_type_name": Attr.get(stock, 'SECURITY_TYPEE', ''),
                "currency": Attr.get(stock, 'CURRENCY', ''),
                "cached": 1,
            }
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.warning(f"获取股票数据出错[EM]<{symbol}> - {err}", 'GET_STOCK_ERR')
            return {}
        return stock_info

    @Ins.cached('GPL_STOCK_INFO_XQ')
    def get_stock_xq(self, code):
        """
        获取雪球股票数据
        数据来源 - https://xueqiu.com/snowman/S/SH603777/detail
        :param code: 股票代码，不带市场前缀，如 603777
        :return: 标准股票数据
        """
        code = self.sft.remove_stock_prefix(code)
        symbol = self.sft.add_stock_prefix(code)
        try:
            stock = self.ak.stock_individual_basic_info_xq(symbol)
            stock = {d['item']: d['value'] for d in stock}
            if not stock.get('org_name_cn'):
                logger.warning(f"获取股票数据失败[AK]<{symbol}> - {stock}", 'GET_STOCK_WAR')
                return {}
            market = Str.replace_multiple(symbol, [code, '.'])
            province, city = self.sft.extract_province_city(Attr.get(stock, 'office_address_cn', ''))
            reg_time = round(int(Attr.get(stock, 'established_date', 0.0)) / 1000)
            list_time = round(int(Attr.get(stock, 'listed_date', 0.0)) / 1000)
            stock_info = {
                "symbol": symbol,
                "code": code,
                "market": market,
                "org_name": Attr.get(stock, 'org_short_name_cn', ''),
                "org_name_full": Attr.get(stock, 'org_name_cn', ''),
                "org_name_en": Attr.get(stock, 'org_short_name_en', ''),
                "org_name_en_full": Attr.get(stock, 'org_name_en', ''),
                "org_type": Attr.get(stock, 'classi_name', ''),
                "org_description": Attr.get(stock, 'org_cn_introduction', '').strip(),
                "main_business": Attr.get(stock, 'main_operation_business', '').strip(),
                "main_business_full": Attr.get(stock, 'operating_scope', '').strip(),
                "industry_em": Attr.get(stock, 'affiliate_industry', {}).get('ind_name', ''),
                "reg_date": Time.dft(reg_time, '%Y-%m-%d'),
                "list_date": Time.dft(list_time, '%Y-%m-%d'),
                "reg_asset": round(Attr.get(stock, 'reg_asset', 0.0) / 1000000, 6),
                "raise_money": round(Attr.get(stock, 'actual_rc_net_amt', 0.0) / 1000000, 6),
                "issue_vol": round(Attr.get(stock, 'actual_issue_vol', 0.0) / 1000000, 6),
                "issue_price": round(Attr.get(stock, 'issue_price', 0.0), 2),
                "pe_rate": round(Attr.get(stock, 'pe_after_issuing', 0.0), 2),
                "lottery_rate": round(Attr.get(stock, 'online_success_rate_of_issue', 0.0), 2),
                "chairman": Attr.get(stock, 'chairman', ''),
                "actual_managers": Attr.get(stock, 'actual_controller', ''),
                "manager_num": Attr.get(stock, 'executives_nums', ''),
                "general_manager": Attr.get(stock, 'general_manager', ''),
                "legal_representative": Attr.get(stock, 'legal_representative', ''),
                "secretary": Attr.get(stock, 'secretary', ''),
                "staff_num": Attr.get(stock, 'staff_num', 0),
                "website": Attr.get(stock, 'org_website', ''),
                "reg_address": Attr.get(stock, 'reg_address_cn', ''),
                "office_address": Attr.get(stock, 'office_address_cn', ''),
                "province": province,
                "city": city,
                "telephone": Attr.get(stock, 'telephone', ''),
                "fax": Attr.get(stock, 'fax', ''),
                "postcode": Attr.get(stock, 'postcode', ''),
                "email": Attr.get(stock, 'email', ''),
                "concept_code_xq": Attr.get(stock, 'affiliate_industry', {}).get('ind_code', ''),
                "concept_name_xq": Attr.get(stock, 'affiliate_industry', {}).get('ind_name', ''),
                "cached": 1,
            }
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.warning(f"获取股票数据出错[AK]<{symbol}> - {err}", 'GET_STOCK_ERR')
            return {}
        return stock_info

    def get_percent(self, code, code_list, all_code_list):
        """获取进度条"""
        ind = Attr.list_index(all_code_list, code) + 1
        per = f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}%)"
        if code_list:
            per += f" | ({round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)"
        return per
