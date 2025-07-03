from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from model.gpl.gpl_change_log_model import GPLChangeLogModel
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.unit.gpl.ak_data_source import AkDataSource
from tool.unit.gpl.em_data_source import EmDataSource
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


@Ins.singleton
class GPLUpdateService:
    """股票更新类"""

    def __init__(self):
        self.ak = AkDataSource()
        self.em = EmDataSource()

    def quick_update_symbol(self, is_force=0):
        """
        多进程快速更新股票基础数据
        :param is_force: 是否强制更新
        :return:
        """
        code_list = self.get_stock_code_all()
        if not code_list:
            return False
        chunk_list = Attr.chunk_list(code_list)
        # 先删除昨日相关概念板块
        # cdb = GPLConceptModel()
        # cdb.del_concept('EM', [])
        for c_list in chunk_list:
            i = int(sum(int(num) for num in c_list)) % 4 + 1
            RedisTaskQueue(f'rtq_gpl_sym{i}_queue').add_task('GPL_SYM', ','.join(c_list), is_force)
        return True

    def get_stock_code_all(self):
        """
        获取所有股票代码列表 - 不含市场标识
        :return: 股票代码列表
        """
        code_list = self.ak.stock_info_a_code_name()
        return [str(item['code']) for item in code_list]

    def get_stock_info(self, code):
        """
        获取股票数据
        数据来源 - https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=SZ300126&color=b#/gsgk
        :param code: 股票代码，不带市场前缀，如 603777
        :return: 标准股票数据
        """
        Time.sleep(0.1)
        code = Str.remove_stock_prefix(code)
        symbol = Str.add_stock_prefix(code)
        try:
            stock = self.em.get_basic_info(symbol)
            issue = self.em.get_issue_info(symbol)
            # 概念板块和股东 在入库后 再进行更新 - 标志位，更新进度
            # print(stock)
            if not stock.get('SECURITY_NAME_ABBR') or not issue.get('FOUND_DATE'):
                logger.warning(f"获取股票数据失败<{symbol}> - {stock}", 'GET_STOCK_WAR')
                return {}
            market = Str.replace_multiple(symbol, [code, '.'])
            province, city = Str.extract_province_city(Attr.get(stock, 'ADDRESS', ''))
            reg_time = Time.tfd(Attr.get(stock, 'FOUND_DATE'))
            list_time = Time.tfd(Attr.get(stock, 'LISTING_DATE'))
            stock_info = {
                "symbol": symbol,
                "code": code,
                "market": market,
                "org_name": Attr.get(stock, 'SECURITY_NAME_ABBR', ''),
                "org_name_full": Attr.get(stock, 'ORG_NAME', ''),
                "org_name_hist": Attr.get(stock, 'FORMERNAME', ''),
                # "org_name_en": Attr.get(stock, 'org_short_name_en', ''), - xq
                "org_name_en_full": Attr.get(stock, 'ORG_NAME_EN', ''),
                # "org_type": Attr.get(stock, 'classi_name', ''), - xq
                # "concept_code": Attr.get(stock, 'affiliate_industry', {}).get('ind_code', ''), - em - xq
                # "concept_name": Attr.get(stock, 'affiliate_industry', {}).get('ind_name', ''), - em - xq
                "org_description": Attr.get(stock, 'ORG_PROFILE', ''),
                "main_business": Attr.get(stock, 'MAIN_BUSINESS', '').strip(),
                "main_business_full": Attr.get(stock, 'BUSINESS_SCOPE', '').strip(),
                "industry_em": Attr.get(stock, 'EM2016', ''),
                "industry_zjh": Attr.get(stock, 'INDUSTRYCSRC1', ''),
                "reg_date": Time.dft(reg_time, '%Y-%m-%d'),
                "list_date": Time.dft(list_time, '%Y-%m-%d'),
                "reg_asset": round(Attr.get(stock, 'REG_CAPITAL', 0.0) / 100, 6),
                "raise_money": round(Attr.get(issue, 'NET_RAISE_FUNDS', 0.0) / 1000000, 6),
                "issue_vol": round(Attr.get(issue, 'TOTAL_ISSUE_NUM', 0.0) / 1000000, 6),
                "issue_price": round(Attr.get(issue, 'ISSUE_PRICE', 0.0), 2),
                "issue_money": round(Attr.get(issue, 'TOTAL_FUNDS', 0.0) / 1000000, 6),
                "pe_rate": round(Attr.get(issue, 'AFTER_ISSUE_PE', 0.0), 2),
                "lottery_rate": round(Attr.get(issue, 'ONLINE_ISSUE_LWR', 0.0) / 100, 4),
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
            }
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"获取股票数据出错<{symbol}> - {err}", 'GET_STOCK_ERR')
            return {}
        return stock_info

    def update_symbol(self, code_str='', is_force=0):
        """
        更新股票数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param int is_force: 是否强制更新
        :return: 更新结果
        """
        i = 0
        res = {'un_ins_list': []}
        sdb = GPLSymbolModel()
        ldb = GPLChangeLogModel()
        code_list = code_str.split(',') if code_str else self.get_stock_code_all()
        if not code_list:
            return False
        total = len(code_list)
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        for code in code_list:
            i += 1
            Time.sleep(0.1)
            symbol = Str.add_stock_prefix(code)
            try:
                info = Attr.select_item_by_where(s_list, {"symbol": symbol})
                org_name = info.get('org_name') if info else 'None'
                percent = f"[{i}/{total}]({round(100 * i / total, 2)}%)"
                logger.debug(f"更新股票数据<{symbol}>{percent} - {org_name}", 'UP_SYM_INF')
                if info and not is_force:
                    logger.warning(f"已存在股票数据跳过<{symbol}>", 'UP_SYM_WAR')
                    continue
                stock = self.get_stock_info(code)
                if not stock:
                    res['un_ins_list'].append(code)
                    logger.warning(f"更新股票数据失败<{symbol}>", 'UP_SYM_WAR')
                    continue
                if not info:
                    # 新增
                    res['ins_sym'] = sdb.add_symbol(stock)
                else:
                    # 更新
                    change_log = Attr.data_diff(Attr.select_keys(info, stock.keys()), stock)
                    if change_log:
                        before_data = Attr.select_keys(info, change_log.keys())
                        after_data = Attr.select_keys(stock, change_log.keys())
                        clg_info = {
                            "symbol": symbol,
                            "cl_tab": sdb.table_name(),
                            "cl_time": Time.date(),
                            "cl_md5": Str.md5(str(after_data)),
                        }
                        logger.warning(f"股票数据发生变化<{symbol}> - {change_log}", 'UP_SYM_WAR')
                        res['up_sym'] = sdb.update_symbol(symbol, after_data)
                        res['ins_clg'] = ldb.add_change_log(clg_info, before_data, after_data)
            except Exception as e:
                res['un_ins_list'].append(code)
                err = Error.handle_exception_info(e)
                logger.error(f"更新股票数据出错<{symbol}> - {err}", 'UP_SYM_ERR')
                continue
        # 更新额外信息
        i = int(sum(int(num) for num in code_list)) % 4 + 1
        res['up_saf'] = RedisTaskQueue(f'rtq_gpl_saf{i}_queue').add_task('GPL_SAF', code_str)
        return res

    def update_symbol_after(self, code_str):
        """异步更新股票补充数据"""
        res = {}
        code_list = code_str.split(',')
        if not code_list:
            return False
        sdb = GPLSymbolModel()
        kdb = GPLConstKvModel()
        cdb = GPLConceptModel()
        tdb = GPLSymbolTextModel()
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        k_list_xq = kdb.get_const_list('XQ_CONCEPT')
        k_list_em = kdb.get_const_list('EM_CONCEPT')
        c_list_xq = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, 'XQ'), 'symbol')
        c_list_em = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, 'EM'), 'symbol')
        t_list_em = Attr.group_item_by_key(tdb.get_text_list(symbol_list, 'EM_TC'), 'symbol')
        for code in code_list:
            symbol = Str.add_stock_prefix(code)
            info = Attr.select_item_by_where(s_list, {"symbol": symbol})
            if not info:
                logger.warning(f"未查询到股票数据<{symbol}>", 'UP_SAF_WAR')
                return False
            cl_xq = Attr.get(c_list_xq, symbol, [])
            cl_em = Attr.get(c_list_em, symbol, [])
            t_em = Attr.get(t_list_em, symbol, [])
            # 雪球概念更新
            logger.debug(f"异步更新股票数据<{symbol}> - ST", 'UP_SAF_INF')
            res = self.update_by_xq(symbol, info, res, k_list_xq, cl_xq)
            # 东财概念更新
            logger.debug(f"异步更新股票结果<{symbol}> - XQ - {res}", 'UP_SAF_INF')
            res = self.update_by_em(symbol, info, res, k_list_em, cl_em, t_em)
            logger.debug(f"异步更新股票结果<{symbol}> - EM - {res}", 'UP_SAF_INF')
        return res

    def update_by_xq(self, symbol, info, res, k_list_xq, c_list_xq):
        """从雪球中拉取数据进行更新"""
        update_data = {}
        sdb = GPLSymbolModel()
        stock_xq = self.ak.stock_individual_basic_info_xq(symbol)
        if stock_xq:
            if info['org_name_en'] != stock_xq['org_short_name_en']:
                update_data['org_name_en'] = stock_xq['org_short_name_en']
            if info['org_type'] != stock_xq['classi_name']:
                update_data['org_type'] = stock_xq['classi_name']
            concept_code = Attr.get(stock_xq, 'affiliate_industry', {}).get('ind_code', '')
            concept_name = Attr.get(stock_xq, 'affiliate_industry', {}).get('ind_name', '')
            if concept_code and concept_name:
                res['up_concept_xq'] = self.update_concept(symbol, concept_code, concept_name, 'XQ', '', k_list_xq, c_list_xq)
            if update_data:
                res['up_stock_xq'] = sdb.update_symbol(symbol, update_data)
        return res

    def update_by_em(self, symbol, info, res, k_list_em, c_list_em, t_em):
        """从东财中拉取数据进行更新"""
        tdb = GPLSymbolTextModel()
        code = info['code']
        # 概念板块
        ci_info = self.em.get_concept_info(code)
        if ci_info:
            for c in ci_info:
                concept_code = Attr.get(c, 'NEW_BOARD_CODE', '')
                concept_name = Attr.get(c, 'BOARD_NAME', '')
                des = Attr.get(c, 'BOARD_TYPE', '')
                if concept_code and concept_name:
                    res['up_concept_em'] = self.update_concept(symbol, concept_code, concept_name, 'EM', des, k_list_em, c_list_em)
        # 核心题材
        ct_list = self.em.get_concept_text(code)
        if ct_list:
            biz_type = 'EM_TC'
            t_list = t_em
            ct_info = Attr.group_item_by_key(ct_list, 'KEY_CLASSIF')
            for k, v in ct_info.items():
                c = v[0]
                title = Attr.get(c, 'KEY_CLASSIF', '')
                kw = Attr.get(c, 'KEYWORD', '')
                c_text = ''
                for vv in v:
                    text = Attr.get(vv, 'MAINPOINT_CONTENT', '')
                    c_text += "\r\n" if c_text else ""
                    c_text += text if title == kw else f"**{kw}**\r\n{text}"
                if title and c_text:
                    ek = Str.first_py_char(title)
                    d_info = Attr.select_item_by_where(t_list, {'e_key': ek}, {})
                    if not d_info and not tdb.get_text(symbol, biz_type, ek):
                        res['ins_text_em'] = tdb.add_text({
                            "symbol": symbol,
                            "biz_type": biz_type,
                            "e_key": ek,
                            "e_des": title,
                            "e_val": c_text,
                        })
        return res

    def update_concept(self, symbol, code, name, type, des, k_list, c_list):
        """更新股票概念板块"""
        kdb = GPLConstKvModel()
        cdb = GPLConceptModel()
        biz_type = type + '_CONCEPT'
        k_info = Attr.get(k_list, code)
        if not k_info and not kdb.get_const(biz_type, code):
            kdb.add_const({
                "biz_type": biz_type,
                "e_key": code,
                "e_des": des,
                "e_val": name,
            })
        c_info = Attr.select_item_by_where(c_list, {'concept_code': code})
        if not c_info and not cdb.get_concept(symbol, type, code):
            cdb.add_concept({
                "symbol": symbol,
                "source_type": type,
                "concept_code": code,
                "concept_name": name,
            })
        return True
