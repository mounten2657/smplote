from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_symbol_ext_model import GPLSymbolExtModel
from model.gpl.gpl_season_model import GPLSeasonModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from tool.unit.gpl.ak_data_source import AkDataSource
from tool.unit.gpl.em_data_sub_source import EmDataSubSource
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


class GplFormatterService:
    """股票获取类"""

    def __init__(self):
        self.ak = AkDataSource()
        self.em = EmDataSubSource()
        self.sdb = GPLSymbolModel()

    def get_stock(self, code):
        """从数据库中获取股票信息"""
        code = Str.remove_stock_prefix(code)
        symbol = Str.add_stock_prefix(code)
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
        :return: 股票代码列表
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
        code = Str.remove_stock_prefix(code)
        symbol = Str.add_stock_prefix(code)
        try:
            stock = self.em.get_basic_info(symbol)
            issue = self.em.get_issue_info(symbol)
            if not stock.get('SECURITY_NAME_ABBR') or not issue.get('FOUND_DATE'):
                logger.warning(f"获取股票数据失败[EM]<{symbol}> - {stock}", 'GET_STOCK_WAR')
                return {}
            market = Str.replace_multiple(symbol, [code, '.'])
            province, city = Str.extract_province_city(Attr.get(stock, 'ADDRESS', ''))
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
        code = Str.remove_stock_prefix(code)
        symbol = Str.add_stock_prefix(code)
        try:
            stock = self.ak.stock_individual_basic_info_xq(symbol)
            stock = {d['item']: d['value'] for d in stock}
            if not stock.get('org_name_cn'):
                logger.warning(f"获取股票数据失败[AK]<{symbol}> - {stock}", 'GET_STOCK_WAR')
                return {}
            market = Str.replace_multiple(symbol, [code, '.'])
            province, city = Str.extract_province_city(Attr.get(stock, 'office_address_cn', ''))
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

    def update_by_xq(self, symbol, info, k_list_xq, c_list_xq):
        """从雪球中拉取数据进行更新"""
        res = {}
        # 改为只更新一次 - 毕竟不常用
        if k_list_xq and c_list_xq:
            return res
        code = info['code']
        stock = self.get_stock_info(code, 1)
        if stock:
            concept_code = Attr.get(stock, 'concept_code_xq', '')
            concept_name = Attr.get(stock, 'concept_name_xq', '')
            if concept_code and concept_name:
                res['ucx'] = self.update_concept(symbol, concept_code, concept_name, 'XQ', '', k_list_xq, c_list_xq)
        return res

    def update_by_em(self, symbol, info, k_list_em, c_list_em, t_em):
        """从东财中拉取数据进行更新"""
        res = {}
        # 改为只更新一次 - 毕竟不常用
        if k_list_em and c_list_em and t_em:
            return res
        sdb = GPLSymbolModel()
        tdb = GPLSymbolTextModel()
        code = info['code']
        # 概念板块
        ci_info = self.em.get_concept_info(code)
        if ci_info:
            concept_list = []
            for c in ci_info:
                concept_code = Attr.get(c, 'NEW_BOARD_CODE', '')
                concept_name = Attr.get(c, 'BOARD_NAME', '')
                des = Attr.get(c, 'BOARD_TYPE', '')
                if concept_code and concept_name:
                    res['uce'] = self.update_concept(symbol, concept_code, concept_name, 'EM', des, k_list_em, c_list_em)
                    if '昨日' not in concept_name:
                        concept_list.append(concept_name)
            concept_list = ','.join(concept_list)
            if concept_list and info['concept_list'] != concept_list:
                ext = {'update_list': info['update_list'] | {'em': Time.date()}} | {"concept_list": concept_list}
                res['use'] = sdb.update_symbol(symbol, {}, {}, ext)
        # 核心题材
        ct_list = self.em.get_concept_text(code)
        if ct_list:
            biz_code = 'EM_TC'
            t_list = t_em
            t_list = {f"{d['e_key']}": d for d in t_list}
            ct_info = Attr.group_item_by_key(ct_list, 'KEY_CLASSIF')
            for k, v in ct_info.items():
                c = v[0]
                title = Attr.get(c, 'KEY_CLASSIF', '')
                c_text = ''
                for vv in v:
                    kw = Attr.get(vv, 'KEYWORD', '')
                    text = Attr.get(vv, 'MAINPOINT_CONTENT', '')
                    c_text += "\r\n" if c_text else ""
                    c_text += text if title == kw else f"**{kw}**\r\n{text}\r\n"
                if title and c_text:
                    ek = Str.first_py_char(title)
                    d_info = Attr.get(t_list, ek, {})
                    if not d_info and not tdb.get_text(symbol, biz_code, ek):
                        res['ite'] = tdb.add_text({
                            "symbol": symbol,
                            "biz_code": biz_code,
                            "e_key": ek,
                            "e_des": title,
                            "e_val": c_text.strip(),
                        })
        return res

    def update_concept(self, symbol, code, name, type, des, k_list, c_list):
        """更新股票概念板块"""
        kdb = GPLConstKvModel()
        cdb = GPLConceptModel()
        biz_code = type + '_CONCEPT'
        k_info = Attr.get(k_list, code)
        c_list = {f"{d['concept_code']}": d for d in c_list}
        if not k_info and not kdb.get_const(biz_code, code):
            kdb.add_const({
                "biz_code": biz_code,
                "e_key": code,
                "e_des": des,
                "e_val": name,
            })
        c_info = Attr.get(c_list, code)
        if not c_info and not cdb.get_concept(symbol, type, code):
            cdb.add_concept({
                "symbol": symbol,
                "source_type": type,
                "concept_code": code,
                "concept_name": name,
            })
        return True

    def get_percent(self, code, code_list, all_code_list):
        """获取进度条"""
        ind = Attr.list_index(all_code_list, code) + 1
        return (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                   f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")

    def update_change_log(self, symbol, info):
        """更新股票变更日志"""
        ret = {}
        sdb = GPLSymbolModel()
        jdb = GPLSeasonModel()
        edb = GPLSymbolExtModel()
        s_biz_list = ['EM_GD_TOP10', 'EM_GD_TOP10_FREE']
        e_biz_list = ['EM_GD_NUM', 'EM_GD_ORG_T', 'EM_GD_ORG_D', 'EM_GD_ORG_L']
        for biz_code in s_biz_list:
            key = 'gd_top10_list' if 'EM_GD_TOP10' == biz_code else 'gd_top10_free_list'
            g_info = jdb.get_season_recent(symbol, biz_code, key)
            if not g_info:
                logger.debug(f"暂无股票季度数据<{symbol}><{biz_code} / {key}>", 'UP_EGD_SKP')
                continue
            gd_list = ','.join([f"{b['gd_name']}:{b['rate']}%" for b in g_info['e_val']])
            if gd_list and info[key] != gd_list:
                after = {key: gd_list}
                before = {key: info[key]} if info[key] else {}
                ext = {'update_list': info['update_list'] | {'gd': Time.date()}}
                ret['ugd'] = sdb.update_symbol(symbol, after, before, ext)
        for biz_code in e_biz_list:
            key = biz_code.lower()
            g_info = jdb.get_season_recent(symbol, biz_code, key)
            if not g_info:
                logger.debug(f"暂无股票季度数据<{symbol}><{biz_code} / {key}>", 'UP_EGE_SKP')
                continue
            e_info = edb.get_ext(symbol, biz_code, key)
            if not e_info:
                insert = {
                    "symbol": symbol,
                    "biz_code": biz_code,
                    "e_key": g_info.get('e_key', ''),
                    "e_des": g_info.get('e_des', ''),
                    "e_val": g_info.get('e_val', ''),
                    "sid": g_info.get('id', 0),
                    "std": g_info.get('season_date', Time.date('%Y-%m-%d')),
                }
                ret['ige'] = edb.add_ext(insert)
            else:
                if g_info['e_val'] != e_info['e_val']:
                    after = {key: g_info['e_val']}
                    before = {key: e_info['e_val']}
                    ret['uge'] = edb.update_ext(e_info['id'], symbol, key, after, before)
        return ret

