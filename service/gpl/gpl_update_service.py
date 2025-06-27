from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_concept_model import GPLConceptModel
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.unit.gp.akshare_data import AkshareData
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


@Ins.singleton
class GPLUpdateService:

    def __init__(self):
        self.client = AkshareData()

    def quick_update_symbol(self):
        """多进程快速更新股票基础数据"""
        code_list = self.get_stock_code_all()
        if not code_list:
            return False
        chunk_list = Attr.chunk_list(code_list)
        for c_list in chunk_list:
            i = int(sum(int(num) for num in c_list)) % 4 + 1
            RedisTaskQueue(f'rtq_gpl_sym{i}_queue').add_task('GPL_SYM', ','.join(c_list))
        return True

    def get_stock_code_all(self):
        """
        获取所有股票代码列表 - 不含市场标识
        :return: 股票代码列表
        """
        code_list = self.client.stock_info_a_code_name()
        return [str(item['code']) for item in code_list]

    def get_stock_info(self, code):
        """
        获取股票数据
        数据来源 - https://xueqiu.com/snowman/S/SH603777/detail
        :param code: 股票代码，不带市场前缀，如 603777
        :return: 标准股票数据
        """
        Time.sleep(0.1)
        code = Str.remove_stock_prefix(code)
        symbol = Str.add_stock_prefix(code)
        try:
            stock = self.client.stock_individual_basic_info_xq(symbol)
            stock = {d['item']: d['value'] for d in stock}
            if not stock.get('org_name_cn'):
                logger.warning(f"获取股票数据失败<{symbol}> - {stock}", 'GET_STOCK_WAR')
                return {}
            concept_type = 'XQ'
            market = Str.replace_multiple(symbol, [code, '.'])
            province, city = Str.extract_province_city(Attr.get(stock, 'office_address_cn', ''))
            reg_date = int(Attr.get(stock, 'established_date', 0.0))
            list_date = int(Attr.get(stock, 'listed_date', 0.0))
            # print(stock)
            stock_info = {
                "symbol": symbol,
                "code": code,
                "market": market,
                "org_name": Attr.get(stock, 'org_short_name_cn', ''),
                "org_name_full": Attr.get(stock, 'org_name_cn', ''),
                "org_name_en": Attr.get(stock, 'org_short_name_en', ''),
                "org_name_en_full": Attr.get(stock, 'org_name_en', ''),
                "org_type": Attr.get(stock, 'classi_name', ''),
                "concept_code": Attr.get(stock, 'affiliate_industry', {}).get('ind_code', ''),
                "concept_name": Attr.get(stock, 'affiliate_industry', {}).get('ind_name', ''),
                "concept_type": concept_type,
                "org_description": Attr.get(stock, 'org_cn_introduction', ''),
                "main_business": Attr.get(stock, 'main_operation_business', '').strip(),
                "main_business_full": Attr.get(stock, 'operating_scope', '').strip(),
                "reg_date": Time.dft(round((reg_date if reg_date > 0 else 0) / 1000)),
                "list_date": Time.dft(round((list_date if list_date > 0 else 0) / 1000)),
                "reg_asset": round(Attr.get(stock, 'reg_asset', 0.0) / 1000000, 6),
                "raise_money": round(Attr.get(stock, 'actual_rc_net_amt', 0.0) / 1000000, 6),
                "issue_vol": round(Attr.get(stock, 'actual_issue_vol', 0.0) / 1000000, 6),
                "issue_price": round(Attr.get(stock, 'issue_price', 0.0), 2),
                "pe_rate": round(Attr.get(stock, 'pe_after_issuing', 0.0), 2),
                "lottery_rate": round(Attr.get(stock, 'online_success_rate_of_issue', 0.0) * 100, 2),
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
            }
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"获取股票数据出错<{symbol}> - {err}", 'GET_STOCK_ERR')
            return {}
        return stock_info

    def update_symbol(self, code_str, is_force=0):
        """
        更新股票数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param int is_force: 是否强制更新
        :return: 更新结果
        """
        i = 0
        res = {}
        sdb = GPLSymbolModel()
        code_list = code_str.split(',')
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
                    continue
                stock = self.get_stock_info(code)
                if not stock:
                    logger.warning(f"更新股票数据失败<{symbol}>", 'UP_SYM_WAR')
                    continue
                if not info:
                    # 新增
                    res['ins_sym'] = sdb.add_symbol(stock)
                    res['up_con'] = self.update_concept(stock)
                else:
                    # 更新
                    change_log = Attr.data_diff(Attr.select_keys(info, stock.keys()), stock)
                    if change_log:
                        update_data = Attr.select_keys(stock, change_log.keys())
                        info['change_log'].append(change_log)
                        if len(info['change_log']) > 30:
                            info['change_log'].pop(0)
                        update_data['change_log'] = info['change_log']
                        res['update_data'] = update_data
                        res['up_sym'] = sdb.update_symbol(symbol, update_data)
            except Exception as e:
                err = Error.handle_exception_info(e)
                logger.error(f"更新股票数据出错<{symbol}> - {err}", 'UP_SYM_ERR')
                continue
        return res

    def update_concept(self, data):
        """更新股票概念板块"""
        cdb = GPLConceptModel()
        keys = ['concept_code', 'concept_type', 'concept_name']
        if not Attr.has_keys(data, keys):
            return False
        c_data = Attr.select_keys(data, keys)
        concept_code, concept_type, concept_name = c_data.values()
        c_info = cdb.get_concept(concept_code, concept_type)
        if not c_info:
            cdb.add_concept(c_data)
        else:
            if Attr.data_diff(c_data, Attr.select_keys(c_info, keys)):
                cdb.update_concept(c_info['id'], c_data)
        return True


