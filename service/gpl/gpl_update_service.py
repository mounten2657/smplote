from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from model.gpl.gpl_symbol_ext_model import GPLSymbolExtModel
from model.gpl.gpl_daily_model import GPLDailyModel
from model.gpl.gpl_api_log_model import GplApiLogModel
from model.gpl.gpl_season_model import GPLSeasonModel
from tool.db.cache.redis_client import RedisClient
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


@Ins.singleton
class GPLUpdateService:
    """股票更新类"""

    # 初始化的开始结束日期
    _INIT_ST = '2000-01-01'
    _INIT_ET = '2025-07-31'

    # 无法正常获取股东信息的股票列表
    _S_GD_LIST = [
        "SH688755","SH603382","SZ301590","SH603014","SZ301636","SZ301662","SZ301678","SH688729","SZ301630","SH603262",
        "BJ920027", "BJ920037", "BJ920068", "BJ920108", "SH600930","SZ001400", "SZ301609"
    ]

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
        code_list = [Str.remove_stock_prefix(c) for c in code_list]
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        s_list = {f"{d['symbol']}": d for d in s_list}

        @Ins.multiple_executor(10)
        def _up_sym_exec(code):
            res = {'ul': []}
            Time.sleep(Str.randint(1, 10) / 100)
            symbol = Str.add_stock_prefix(code)
            try:
                info = Attr.get(s_list, symbol)
                org_name = info.get('org_name') if info else 'None'
                percent = self._get_percent(code, code_list, all_code_list)
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
                    res['ins'] = sdb.add_symbol(stock | ext)
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
                        res['ups'] = sdb.update_symbol(symbol, after, before, ext)
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
        jdb = GPLSeasonModel()
        code_list = [Str.remove_stock_prefix(c) for c in code_list]
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        k_list_em = kdb.get_const_list('EM_CONCEPT')
        c_list_em = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, 'EM'), 'symbol')
        t_list_em = Attr.group_item_by_key(tdb.get_text_list(symbol_list, 'EM_TC'), 'symbol')
        s_list = {f"{d['symbol']}": d for d in s_list}
        if Time.date('%Y-%m-%d') <= self._INIT_ET:
            k_list_xq = kdb.get_const_list('XQ_CONCEPT')
            c_list_xq = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, 'XQ'), 'symbol')

        day_list = []
        n = 102 if is_force > 90 else 3
        is_all = int(is_force > 90)
        for nn in range(1, n + 1):
            day_list.append(Time.recent_season_day(nn))
        day_list.reverse()
        day = int(Time.date('%d'))
        td = Time.date('%Y-%m-%d')
        check_day = [1, 10, 20]
        if is_force > 90:  # 初始化
            check_day = range(1, 32)
            td = self._INIT_ET
        if day in check_day:
            tdl = [] if is_all else day_list
            cdl = [Time.date('%Y-%m') + f"-{chd:02d}" for chd in check_day]
            md = Time.dft(Time.tfd(self._INIT_ST if is_all else td, '%Y-%m-%d') - 30 * 86400, '%Y-%m-%d')
            if 0 == is_force or 91 == is_force:
                gd_list = jdb.get_season_list(symbol_list, tdl, 'EM_GD_TOP10')
                gd_list_free = jdb.get_season_list(symbol_list, tdl, 'EM_GD_TOP10_FREE')
            if 0 == is_force or 92 == is_force:
                gdn_list = jdb.get_season_list(symbol_list, tdl, 'EM_GD_NUM')
            if 0 == is_force or 93 == is_force:
                gdt_list = jdb.get_season_list(symbol_list, tdl, 'EM_GD_ORG_T')
            if 0 == is_force or 94 == is_force:
                gdd_list = jdb.get_season_list(symbol_list, tdl, 'EM_GD_ORG_D')
            if 0 == is_force or 95 == is_force:
                gdl_list = jdb.get_season_list(symbol_list, tdl, 'EM_GD_ORG_L')
            if 0 == is_force or 96 == is_force:
                dvo_list = jdb.get_season_list(symbol_list, cdl, 'EM_DV_OV')
                dvt_list = jdb.get_season_list(symbol_list, cdl, 'EM_DV_OV_TEXT')
            if 0 == is_force or 97 == is_force:
                dvh_list = jdb.get_season_list(symbol_list, [], 'EM_DV_HIST', md)
            if 0 == is_force or 98 == is_force:
                dvr_list = jdb.get_season_list(symbol_list, [], 'EM_DV_HIST_R', md)
            if 0 == is_force or 99 == is_force:
                dvp_list = jdb.get_season_list(symbol_list, [], 'EM_DV_HIST_P', md)

        @Ins.multiple_executor(10)
        def _up_saf_exec(code):
            Time.sleep(Str.randint(1, 10) / 100)
            ret = {}
            symbol = Str.add_stock_prefix(code)
            info = Attr.get(s_list, symbol)
            percent = self._get_percent(code, code_list, all_code_list)
            if not info:
                logger.warning(f"未查询到股票数据<{symbol}>{percent}", 'UP_SAF_WAR')
                return False
            cl_em = Attr.get(c_list_em, symbol, [])
            t_em = Attr.get(t_list_em, symbol, [])
            logger.debug(f"更新股票额外数据<{symbol}>{percent} - STA", 'UP_SAF_INF')
            # 季度相关数据
            if day in check_day:
                is_special = int(symbol in self._S_GD_LIST)
                sd_list = [Time.date('%Y-%m-%d') if not is_force else self._INIT_ET] if is_special else day_list
                # 东财十大股东更新
                if 0 == is_force or 91 == is_force:
                    ret = ret | self._up_gd_em(symbol, gd_list, gd_list_free, sd_list, n, is_special)
                    logger.debug(f"更新十大股东结果<{symbol}>{percent} - GD - {ret}", 'UP_SAF_INF')
                # 东财股东人数合计更新
                if 0 == is_force or 92 == is_force:
                    ret = ret | self._up_gdn_em(symbol, gdn_list, sd_list, n, is_special)
                    logger.debug(f"更新股东人数合计结果<{symbol}>{percent} - GN - {ret}", 'UP_SAF_INF')
                # 东财股东机构合计更新
                if 0 == is_force or 93 == is_force:
                    ret = ret | self._up_gdt_em(symbol, gdt_list, day_list)
                    logger.debug(f"更新股东机构合计结果<{symbol}>{percent} - GT - {ret}", 'UP_SAF_INF')
                # 东财股东机构明细更新
                if 0 == is_force or 94 == is_force:
                    ret = ret | self._up_gdd_em(symbol, gdd_list, day_list)
                    logger.debug(f"更新股东机构明细结果<{symbol}>{percent} - GA - {ret}", 'UP_SAF_INF')
                # 东财股东机构列表更新
                if 0 == is_force or 95 == is_force:
                    ret = ret | self._up_gdl_em(symbol, gdl_list, day_list)
                    logger.debug(f"更新股东机构列表结果<{symbol}>{percent} - GL - {ret}", 'UP_SAF_INF')
                # 东财分红概览更新
                if 0 == is_force or 96 == is_force:
                    ret = ret | self._up_dvo_em(symbol, dvo_list, dvt_list, td)
                    logger.debug(f"更新分红概览结果<{symbol}>{percent} - DO - {ret}", 'UP_SAF_INF')
                # 东财分红历史更新
                if 0 == is_force or 97 == is_force:
                    ret = ret | self._up_dvh_em(symbol, dvh_list, td, n)
                    logger.debug(f"更新分红历史结果<{symbol}>{percent} - DH - {ret}", 'UP_SAF_INF')
                # 东财分红股息率更新
                if 0 == is_force or 98 == is_force:
                    ret = ret | self._up_dvr_em(symbol, dvr_list, self._INIT_ST, self._INIT_ET)
                    logger.debug(f"更新分红股息率结果<{symbol}>{percent} - DH - {ret}", 'UP_SAF_INF')
                # 东财分红股利支付率更新
                if 0 == is_force or 99 == is_force:
                    ret = ret | self._up_dvp_em(symbol, dvp_list, self._INIT_ST, self._INIT_ET)
                    logger.debug(f"更新分红股利支付率结果<{symbol}>{percent} - DH - {ret}", 'UP_SAF_INF')
            # 雪球概念更新
            if Time.date('%Y-%m-%d') <= self._INIT_ET:
                cl_xq = Attr.get(c_list_xq, symbol, [])
                ret = ret | self._update_by_xq(symbol, info, k_list_xq, cl_xq)
                logger.debug(f"更新股票雪概结果<{symbol}>{percent} - XQ - {ret}", 'UP_SAF_INF')
            # 东财概念更新
            ret = ret | self._update_by_em(symbol, info, k_list_em, cl_em, t_em)
            logger.debug(f"更新股票东概结果<{symbol}>{percent} - EM - {ret}", 'UP_SAF_INF')
            # 变更日志更新
            if not is_force:
                ret = ret | self._update_change_log(symbol, info)
                logger.debug(f"更新股票变更结果<{symbol}>{percent} - CL - {ret}", 'UP_SAF_INF')
            return ret

        return _up_saf_exec(code_list)

    def update_symbol_daily(self, code_str, is_force=0):
        """
        更新股票日线数据
        :param code_str: 股票代码列表，一般是50个
        :param is_force:  99: 仅拉取股票历史数据 | 98: 对历史数据入库 | 0, 15: 更新最近五天 | 10: 今日 | 17: 最近一周
        :return:
        """
        code_list = code_str.split(',')
        if not code_list:
            return False
        all_code_list = self.formatter.get_stock_code_all()
        code_list = [Str.remove_stock_prefix(c) for c in code_list]
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]

        n = 5 if is_force == 0 else is_force - 10
        st = Time.dft(Time.now() - n * 86400, '%Y-%m-%d')
        et = Time.date('%Y-%m-%d')
        if is_force > 90:  # 初始化
            st = self._INIT_ST
            et = self._INIT_ET
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

        @Ins.multiple_executor(10)
        def _up_day_exec(code):
            Time.sleep(Str.randint(1, 10) / 100)
            res = []
            symbol = Str.add_stock_prefix(code)
            percent = self._get_percent(code, code_list, all_code_list)
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
                logger.debug(f"接口请求日线数据<{symbol}><{tds}>{percent} - {k}"
                             f" - [{len(day_list)}]", 'UP_DAY_SKP')
                if not day_list:
                    logger.warning(f"暂无日线数据<{symbol}><{tds}>{percent}", 'UP_DAY_WAR')
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

    def _get_percent(self, code, code_list, all_code_list):
        """获取进度条"""
        ind = Attr.list_index(all_code_list, code) + 1
        return (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                   f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")

    def _update_by_xq(self, symbol, info, k_list_xq, c_list_xq):
        """从雪球中拉取数据进行更新"""
        res = {}
        # 改为只更新一次 - 毕竟不常用
        if k_list_xq and c_list_xq:
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
        # 改为只更新一次 - 毕竟不常用
        if k_list_em and c_list_em and t_em:
            return res
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

    def _update_concept(self, symbol, code, name, type, des, k_list, c_list):
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

    def _update_change_log(self, symbol, info):
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

    def _up_gd_em(self, symbol, gd_list, gd_list_free, day_list, n, is_special):
        """更新股票十大股东"""
        ret = {}
        jdb = GPLSeasonModel()
        s_gd_list = Attr.group_item_by_key(gd_list.values(), 'symbol').get(symbol, [])
        s_gd_list_free = Attr.group_item_by_key(gd_list_free.values(), 'symbol').get(symbol, [])
        s_gd_day = min(v["season_date"] for v in s_gd_list) if s_gd_list else ''
        s_gd_day_free = min(v["season_date"] for v in s_gd_list_free) if s_gd_list_free else ''
        gd_index = [
            {'biz_code': 'EM_GD_TOP10', 'd_list': gd_list, 'des': '十大股东', 'key': 'gd_top10_list', 'min_day': s_gd_day},
            {'biz_code': 'EM_GD_TOP10_FREE', 'd_list': gd_list_free, 'des': '十大流通股东', 'key': 'gd_top10_free_list', 'min_day': s_gd_day_free}
        ]
        for day in day_list:
            for d in gd_index:
                if day < d['min_day']:
                    logger.debug(f"跳过十大股东数据<{symbol}><{day} / {d['min_day']}>", 'UP_GD_SKP')
                    continue
                Time.sleep(Str.randint(1, 5) / 10)
                key = d['key']
                des = d['des']
                biz_code = d['biz_code']
                gd = Attr.get(d['d_list'], f"{symbol}_{day}")
                if not gd:
                    if biz_code == 'EM_GD_TOP10':
                        g_info = self.formatter.em.get_gd_top10(symbol, day, n, is_special)
                    else:
                        g_info = self.formatter.em.get_gd_top10_free(symbol, day)
                    if not g_info:
                        logger.warning(f"暂无十大股东数据<{symbol}><{day}> - {biz_code} - {des}", 'UP_GD_WAR')
                        continue
                    g_list = Attr.group_item_by_key(g_info, 'date')
                    for d2, g2 in g_list.items():
                        gd = Attr.get(d['d_list'], f"{symbol}_{d2}")
                        if not gd:
                            # g2 = [Attr.remove_keys(g3, ['date']) for g3 in g2]
                            g2 = [{**g3, "rank": Attr.get(g3, 'rank', i + 1)} for i, g3 in enumerate(g2)]
                            biz_data = {'key': key, 'des': des, 'val': g2}
                            ret['igd'] = jdb.add_season(symbol, d2, biz_code, biz_data)
        return ret

    def _up_gdn_em(self, symbol, gdn_list, day_list, n, is_special):
        """更新股票股东人数"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        biz_code = 'EM_GD_NUM'
        s_d_list = Attr.group_item_by_key(gdn_list.values(), 'symbol').get(symbol, [])
        s_m_day = min(v["season_date"] for v in s_d_list) if s_d_list else ''
        for td in day_list:
            gdn_info = Attr.get(gdn_list, f"{symbol}_{td}")
            if gdn_info or td < s_m_day:
                logger.warning(f"跳过股东人数合计数据<{symbol}><{td}>", 'UP_GDN_SKP')
                continue
            g_info = self.formatter.em.get_gd_num(symbol, td, n, is_special)
            if not g_info:
                logger.warning(f"暂无股东人数合计数据<{symbol}><{td}>", 'UP_GDN_WAR')
                continue
            for d in g_info:
                gdn_info = Attr.get(gdn_list, f"{symbol}_{d['date']}")
                if not gdn_info:
                    biz_data = {'key': biz_code.lower(), 'des': '股东人数合计', 'val': d}
                    ret['ign'] = jdb.add_season(symbol, d['date'], biz_code, biz_data)
        return ret

    def _up_gdt_em(self, symbol, gdt_list, day_list):
        """更新股票股东机构合计"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        biz_code = 'EM_GD_ORG_T'
        s_d_list = Attr.group_item_by_key(gdt_list.values(), 'symbol').get(symbol, [])
        s_m_day = min(v["season_date"] for v in s_d_list) if s_d_list else ''
        for td in day_list:
            gdt_info = Attr.get(gdt_list, f"{symbol}_{td}")
            if gdt_info or td < s_m_day:
                logger.warning(f"跳过股东机构合计数据<{symbol}><{td}>", 'UP_GDT_SKP')
                continue
            g_info = self.formatter.em.get_gd_org_total(symbol, td)
            if not g_info:
                logger.warning(f"暂无股东机构合计数据<{symbol}><{td}>", 'UP_GDT_WAR')
                return ret
            for d in g_info:
                gdt_info = Attr.get(gdt_list, f"{symbol}_{d['date']}")
                if not gdt_info:
                    biz_data = {'key': biz_code.lower(), 'des': '股东机构合计', 'val': d}
                    ret['igt'] = jdb.add_season(symbol, d['date'], biz_code, biz_data)
        return ret

    def _up_gdd_em(self, symbol, gdd_list, day_list):
        """更新股票股东机构明细"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        biz_code = 'EM_GD_ORG_D'
        s_d_list = Attr.group_item_by_key(gdd_list.values(), 'symbol').get(symbol, [])
        s_m_day = min(v["season_date"] for v in s_d_list) if s_d_list else ''
        for sd in day_list:
            gdd_info = Attr.get(gdd_list, f"{symbol}_{sd}")
            if gdd_info or sd < s_m_day:
                logger.warning(f"跳过股东机构明细数据<{symbol}><{sd}>", 'UP_GDD_SKP')
                continue
            g_info = self.formatter.em.get_gd_org_detail(symbol, sd)
            if not g_info:
                logger.warning(f"暂无股东机构明细数据<{symbol}><{sd}>", 'UP_GDD_WAR')
                continue
            for day, d in g_info.items():
                gdd_info = Attr.get(gdd_list, f"{symbol}_{day}")
                if not gdd_info:
                    biz_data = {'key': biz_code.lower(), 'des': '股东机构明细', 'val': d}
                    ret['iga'] = jdb.add_season(symbol, day, biz_code, biz_data)
        return ret

    def _up_gdl_em(self, symbol, gdd_list, day_list):
        """更新股票股东机构l列表"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        biz_code = 'EM_GD_ORG_L'
        s_d_list = Attr.group_item_by_key(gdd_list.values(), 'symbol').get(symbol, [])
        s_m_day = min(v["season_date"] for v in s_d_list) if s_d_list else ''
        for sd in day_list:
            gdl_info = Attr.get(gdd_list, f"{symbol}_{sd}")
            if gdl_info or sd < s_m_day:
                logger.warning(f"跳过股东机构列表数据<{symbol}><{sd}>", 'UP_GDL_WAR')
                continue
            g_info = self.formatter.em.get_gd_org_list(symbol, sd)
            if not g_info:
                logger.warning(f"暂无股东机构列表数据<{symbol}><{sd}>", 'UP_GDL_WAR')
                continue
            for day, d in g_info.items():
                gdl_info = Attr.get(gdd_list, f"{symbol}_{day}")
                if not gdl_info:
                    biz_data = {'key': biz_code.lower(), 'des': '股东机构列表', 'val': d}
                    ret['igl'] = jdb.add_season(symbol, day, biz_code, biz_data)
        return ret

    def _up_dvo_em(self, symbol, dvo_list, dvt_list, td):
        """更新股票分红概览"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        dv_index = [
            {'biz_code': 'EM_DV_OV', 'd_list': dvo_list, 'des': '分红概览', 'key': 'em_dv_ov'},
            {'biz_code': 'EM_DV_OV_TEXT', 'd_list': dvt_list, 'des': '分红概览描述', 'key': 'em_dv_ov_text'}
        ]
        for d in dv_index:
            biz_code = d['biz_code']
            dv_info = Attr.get(d['d_list'], f"{symbol}_{td}")
            if not dv_info:
                if 'EM_DV_OV' == biz_code:
                    d_info = self.formatter.em.get_dv_ov(symbol, td)
                else:
                    d_info = self.formatter.em.get_dv_ov_text(symbol, td)
                if d_info:
                    biz_data = {'key': d['key'], 'des': d['des'], 'val': d_info}
                    ret['ido'] = jdb.add_season(symbol, td, biz_code, biz_data)
        return ret

    def _up_dvh_em(self, symbol, dvh_list, td, n):
        """更新股票分红历史"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '分红历史'
        biz_code = 'EM_DV_HIST'
        d_info = self.formatter.em.get_dv_hist(symbol, td, n)
        if not d_info:
            logger.warning(f"暂无分红历史数据<{symbol}><{td}> - {n}", 'UP_DVH_WAR')
            return ret
        for day, d in d_info.items():
            dv_info = Attr.get(dvh_list, f"{symbol}_{day}")
            if dv_info or day < self._INIT_ST:
                logger.warning(f"跳过分红历史数据<{symbol}><{day}>", 'UP_DVH_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入分红历史数据<{symbol}><{td}> - {len(d_info)}", 'UP_DVH_WAR')
        ret['idh'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def _up_dvr_em(self, symbol, dvr_list, td, ed):
        """更新股票分红股息率"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '分红股息率'
        biz_code = 'EM_DV_HIST_R'
        d_info = self.formatter.em.get_dv_hist_rate(symbol, td, ed)
        if not d_info:
            logger.warning(f"暂无分红股息率数据<{symbol}><{td}> - {ed}", 'UP_DVR_WAR')
            return ret
        for day in list(d_info.keys()):
            dv_info = Attr.get(dvr_list, f"{symbol}_{day}")
            if dv_info or day < self._INIT_ST:
                logger.warning(f"跳过分红股息率数据<{symbol}><{day}>", 'UP_DVR_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入分红股息率数据<{symbol}><{td}> - {len(d_info)}", 'UP_DVP_WAR')
        ret['idr'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def _up_dvp_em(self, symbol, dvp_list, td, ed):
        """更新股票分红股利支付率"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '分红股利支付率'
        biz_code = 'EM_DV_HIST_P'
        d_info = self.formatter.em.get_dv_hist_pay_rate(symbol, td, ed)
        if not d_info:
            logger.warning(f"暂无分红股利支付率数据<{symbol}><{td}> - {ed}", 'UP_DVP_WAR')
            return ret
        for day in list(d_info.keys()):
            dv_info = Attr.get(dvp_list, f"{symbol}_{day}")
            if dv_info or day < self._INIT_ST:
                logger.warning(f"跳过分红股利支付率数据<{symbol}><{day}>", 'UP_DVP_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入分红股利支付率数据<{symbol}><{td}> - {len(d_info)}", 'UP_DVP_WAR')
        ret['idp'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

