from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from model.gpl.gpl_daily_model import GPLDailyModel
from model.gpl.gpl_api_log_model import GplApiLogModel
from tool.db.cache.redis_client import RedisClient
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


@Ins.singleton
class GPLUpdateService:
    """股票更新类"""

    def __init__(self):
        self.formatter = GplFormatterService()

    def quick_update_symbol(self, code_str='', is_force=0, sk='GPL_SYM'):
        """
        多进程快速更新股票基础数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param is_force: 是否强制更新
        :param sk: 更新类型
        :return:
        """
        code_list = code_str.split(',') if code_str else self.formatter.get_stock_code_all()
        logger.warning(f"总股票数据 - {len(code_list)}", 'UP_SYM_TOL')
        if not code_list:
            return False
        chunk_list = Attr.chunk_list(code_list)
        if 'GPL_SYM' == sk and not code_str:
            # 删除昨日相关概念板块
            cdb = GPLConceptModel()
            d_count = cdb.del_concept_yesterday('EM')
            logger.warning(f"删除昨日板块 - {d_count}", 'UP_SYM_YST')
        # 快速转入批量队列中执行
        for c_list in chunk_list:
            RedisTaskQueue.add_task_batch(sk, ','.join(c_list), is_force)
        return True

    def update_symbol(self, code_str, is_force=0):
        """
        更新股票数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param int is_force: 是否强制更新
        :return: 更新结果
        """
        sdb = GPLSymbolModel()
        code_list = code_str.split(',')
        if not code_list:
            return False
        all_code_list = self.formatter.get_stock_code_all()
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        s_list = {f"{d['symbol']}": d for d in s_list}

        @Ins.multiple_executor(5)
        def _up_sym_exec(code):
            res = {'ul': []}
            Time.sleep(Str.randint(1, 10) / 100)
            symbol = Str.add_stock_prefix(code)
            try:
                info = Attr.get(s_list, symbol)
                org_name = info.get('org_name') if info else 'None'
                ind = all_code_list.index(code) + 1
                percent = (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                           f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")
                logger.debug(f"更新股票数据<{symbol}>{percent} - {org_name}", 'UP_SYM_INF')
                if info and not is_force:
                    logger.warning(f"已存在股票数据跳过<{symbol}>", 'UP_SYM_SKP')
                    return False
                # 删除缓存
                if is_force and 6 > int(Time.date('%H')):
                    key_list = ['GPL_STOCK_INFO_XQ', 'GPL_STOCK_INFO_EM']
                    list(map(lambda key: RedisClient().delete(key, [code]), key_list))
                stock = self.formatter.get_stock_info(code)
                if not stock:
                    res['ul'].append(code)
                    logger.warning(f"未能更新的股票数据<{symbol}>", 'UP_SYM_WAR')
                    return False
                if not info:
                    # 新增
                    ext = {'update_list': {'cf': Time.date()}}
                    res['is'] = sdb.add_symbol(stock | ext)
                else:
                    # 更新
                    change_log = Attr.data_diff(Attr.select_keys(info, stock.keys()), stock)
                    # 去除值为0或空的键，防止没有数据而误更新
                    k_list = [k for k, v in change_log.items() if stock[k]]
                    change_log = Attr.select_keys(change_log, k_list)
                    if change_log:
                        before = Attr.select_keys(info, change_log.keys())
                        after = Attr.select_keys(stock, change_log.keys())
                        ext = {'update_list': info['update_list'] | {'uf': Time.date()}}
                        logger.warning(f"股票数据发生变化<{symbol}> - {change_log}", 'UP_SYM_WAR')
                        res['us'] = sdb.update_symbol(symbol, after, before, ext)
            except Exception as e:
                res['ul'].append(code)
                err = Error.handle_exception_info(e)
                logger.error(f"更新股票数据出错<{symbol}> - {err}", 'UP_SYM_ERR')
            return res

        return _up_sym_exec(code_list)

    def update_symbol_ext(self, code_str, is_force=0):
        """更新股票额外数据 - 多线程"""
        code_list = code_str.split(',')
        if not code_list:
            return False
        all_code_list = self.formatter.get_stock_code_all()
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
        s_list = {f"{d['symbol']}": d for d in s_list}

        @Ins.multiple_executor(5)
        def _up_saf_exec(code):
            symbol = Str.add_stock_prefix(code)
            info = Attr.get(s_list, symbol)
            ind = all_code_list.index(code) + 1
            percent = (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                       f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")
            if not info:
                logger.warning(f"未查询到股票数据<{symbol}>{percent}", 'UP_SAF_WAR')
                return False
            cl_xq = Attr.get(c_list_xq, symbol, [])
            cl_em = Attr.get(c_list_em, symbol, [])
            t_em = Attr.get(t_list_em, symbol, [])
            logger.debug(f"更新股票额外数据<{symbol}>{percent} - STA", 'UP_SAF_INF')
            # 雪球概念更新
            ret = self._update_by_xq(symbol, info, k_list_xq, cl_xq, is_force)
            logger.debug(f"更新股票额外结果<{symbol}>{percent} - XQ - {ret}", 'UP_SAF_INF')
            # 东财概念更新
            ret = ret | self._update_by_em(symbol, info, k_list_em, cl_em, t_em)
            logger.debug(f"更新股票额外结果<{symbol}>{percent} - EM - {ret}", 'UP_SAF_INF')
            return ret

        return _up_saf_exec(code_list)

    def update_symbol_daily(self, code_str, is_force=0):
        """
        更新股票日线数据
        :param code_str: 股票代码列表，一般是50个
        :param is_force:  99: 仅拉取股票历史数据 | 98: 对历史数据入库 | 0,10: 更新今日数据 | 17: 更新最近一周
        :return:
        """
        code_list = code_str.split(',')
        if not code_list:
            return False
        all_code_list = self.formatter.get_stock_code_all()
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]

        n = 0 if is_force == 0 else is_force - 10
        st = Time.dft(Time.now() - n * 86400, '%Y-%m-%d')
        et = Time.date('%Y-%m-%d')
        if is_force > 90:  # 初始化
            st = '2000-01-01'
            et = '2025-07-13'
        tds = f'{st}~{et}'

        # 批量查询数据
        ddb = GPLDailyModel()
        ldb = GplApiLogModel()
        d_list = ddb.get_daily_list(symbol_list, [st, et])
        l_list = {
            'f0': ldb.get_gpl_api_log_list('EM_DAILY_0', symbol_list, [tds]),
            'f1': ldb.get_gpl_api_log_list('EM_DAILY_1', symbol_list, [tds]),
            'f2': ldb.get_gpl_api_log_list('EM_DAILY_2', symbol_list, [tds])
        }

        # 手动建立索引
        d_list = {f"{d['symbol']}_{d['trade_date']}": d for d in d_list}
        l_list['f0'] = {f"{d['h_event']}_{d['h_value']}": d for d in l_list['f0']}
        l_list['f1'] = {f"{d['h_event']}_{d['h_value']}": d for d in l_list['f1']}
        l_list['f2'] = {f"{d['h_event']}_{d['h_value']}": d for d in l_list['f2']}

        @Ins.multiple_executor(3)
        def _up_day_exec(code):
            Time.sleep(Str.randint(1, 10) / 100)
            res = []
            symbol = Str.add_stock_prefix(code)
            ind = all_code_list.index(code) + 1
            percent = (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                       f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")
            logger.debug(f"入库股票日线数据<{symbol}><{tds}>{percent} - STA", 'UP_DAY_INF')
            insert_list = {}
            fq_list = {"": "0", "qfq": "1", "hfq": "2"}
            for k, v in fq_list.items():
                # 先判断是否已入库
                log_info = Attr.get(l_list[f'f{v}'], f"{symbol}_{tds}")
                if is_force == 99 and log_info:
                    logger.debug(f"日线数据已入库<{symbol}><{tds}>{percent}", 'UP_DAY_SKP')
                    continue
                day_list = log_info['process_params'] if (log_info and is_force != 99) else \
                    self.formatter.em.get_daily_quote(code, st, et, k)
                res.append(len(day_list))
                logger.debug(f"接口入库日线数据<{symbol}><{tds}>{percent} - {k}"
                             f" - [{len(day_list)}]", 'UP_DAY_SKP')
                if not day_list:
                    logger.warning(f"接口暂无日线数据<{symbol}><{tds}>{percent}", 'UP_DAY_WAR')
                    continue
                if 99 == is_force:
                    continue
                for i, day in enumerate(day_list):
                    td = day['date']
                    info = Attr.get(d_list, f"{symbol}_{td}")
                    if info:
                        if not i % 25 or is_force < 90:
                            logger.debug(f"已存在日线数据<{symbol}><{td}>{percent}", 'UP_DAY_SKP')
                        continue
                    insert_list[td] = insert_list[td] if Attr.has_keys(insert_list, td) else {}
                    insert_list[td].update({
                        "symbol": symbol,
                        "trade_date": td,
                        f"f{v}_open": day['open'],
                        f"f{v}_close": day['close'],
                        f"f{v}_high": day['high'],
                        f"f{v}_low": day['low'],
                        f"f{v}_volume": day['volume'],
                        f"f{v}_amount": day['amount'],
                        f"f{v}_amplitude": day['amplitude'],
                        f"f{v}_pct_change": day['pct_change'],
                        f"f{v}_price_change": day['price_change'],
                        f"f{v}_turnover_rate": day['turnover_rate'],
                    })
            if insert_list:
                ik = insert_list.keys()
                insert_list = insert_list.values()
                iid = ddb.add_daily(insert_list)
                res.append(iid)
                logger.debug(f"新增股票日线数据<{symbol}><{next(iter(ik))}~{next(reversed(ik))}>{percent}"
                             f" - END - {len(ik)} - {iid}", 'UP_DAY_INF')
            return res

        return _up_day_exec(code_list)

    def _update_by_xq(self, symbol, info, k_list_xq, c_list_xq, is_force):
        """从雪球中拉取数据进行更新"""
        res = {}
        # 改为只更新一次 - 毕竟不常用
        if k_list_xq and c_list_xq and not is_force:
            res['ucx'] = False
            return res
        code = info['code']
        stock = self.formatter.get_stock_info(code, 1)
        if stock:
            concept_code = Attr.get(stock, 'concept_code_xq', '')
            concept_name = Attr.get(stock, 'concept_name_xq', '')
            if concept_code and concept_name:
                res['ucx'] = self._update_concept(symbol, concept_code, concept_name, 'XQ', '', k_list_xq, c_list_xq)
        return res

    def _update_by_em(self, symbol, info, k_list_em, c_list_em, t_em):
        """从东财中拉取数据进行更新"""
        res = {}
        sdb = GPLSymbolModel()
        tdb = GPLSymbolTextModel()
        code = info['code']
        # 概念板块
        ci_info = self.formatter.em.get_concept_info(code)
        if ci_info:
            concept_list = []
            for c in ci_info:
                concept_code = Attr.get(c, 'NEW_BOARD_CODE', '')
                concept_name = Attr.get(c, 'BOARD_NAME', '')
                des = Attr.get(c, 'BOARD_TYPE', '')
                if concept_code and concept_name:
                    res['uce'] = self._update_concept(symbol, concept_code, concept_name, 'EM', des, k_list_em, c_list_em)
                    if '昨日' not in concept_name:
                        concept_list.append(concept_name)
            concept_list = ','.join(concept_list)
            if concept_list and info['concept_list'] != concept_list:
                ext = {'update_list': info['update_list'] | {'em': Time.date()}} | {"concept_list": concept_list}
                res['use'] = sdb.update_symbol(symbol, {}, {}, ext)
        # 核心题材
        ct_list = self.formatter.em.get_concept_text(code)
        if ct_list:
            biz_type = 'EM_TC'
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
                    if not d_info and not tdb.get_text(symbol, biz_type, ek):
                        res['ite'] = tdb.add_text({
                            "symbol": symbol,
                            "biz_type": biz_type,
                            "e_key": ek,
                            "e_des": title,
                            "e_val": c_text.strip(),
                        })
        return res

    def _update_concept(self, symbol, code, name, type, des, k_list, c_list):
        """更新股票概念板块"""
        kdb = GPLConstKvModel()
        cdb = GPLConceptModel()
        biz_type = type + '_CONCEPT'
        k_info = Attr.get(k_list, code)
        c_list = {f"{d['concept_code']}": d for d in c_list}
        if not k_info and not kdb.get_const(biz_type, code):
            kdb.add_const({
                "biz_type": biz_type,
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
