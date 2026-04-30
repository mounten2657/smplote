from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_daily_model import GPLDailyModel
from model.gpl.gpl_api_log_model import GplApiLogModel
from tool.db.cache.redis_client import RedisClient
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.core import Ins, Logger, Str, Time, Attr, Error, Env, Sys

logger = Logger()
redis = RedisClient()


@Ins.singleton
class GPLUpdateService:
    """股票更新类"""

    # 初始化的开始结束日期
    _INIT_ST = GplFormatterService.INIT_ST
    _INIT_ET = GplFormatterService.INIT_ET

    # 重点关注的股票列表
    _S_ZD_LIST = Env.get('GPL_ZD_LIST', '').split(',')

    def __init__(self):
        self.formatter = GplFormatterService()

    def quick_update_symbol(self, code_str='', is_force=0, sk='GPL_SYM', td=None, vip=0):
        """
        多进程快速更新股票基础数据

        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param is_force: 是否强制更新
        :param sk: 更新类型
        :param str td: 当前日期 - %Y-%m-%d
        :param int vip: 是否使用特殊节点请求
        :return:
        """
        # 周末不更新
        if not is_force and Time.is_week():
            return False
        if Str.is_int(td):
            current_date = Time.dnd(int(td))
        else:
            current_date = td if td else Time.date('%Y-%m-%d')
        if code_str.upper() == 'ZD':
            code_list = GPLUpdateService._S_ZD_LIST  # 走快速通道的股票列表
            # 统一格式 - 去除前缀
            code_list = [self.formatter.sft.remove_stock_prefix(c) for c in code_list]
        else:
            code_list = code_str.split(',') if code_str else self.formatter.get_stock_code_all()
        logger.warning(f"[{current_date}]总股票数据 - {len(code_list)}", 'UP_SYM_TOL')
        if not code_list:
            return False
        chunk_list = Attr.chunk_list(code_list)
        if 'GPL_SYM' == sk and not code_str:
            # 删除昨日相关概念板块
            cdb = GPLConceptModel()
            d_count = cdb.del_concept_yesterday('EM')
            logger.warning(f"删除昨日板块 - {d_count}", 'UP_SYM_YST')
        if 'GPL_DAY' == sk and not code_str:
            # 重置计数缓存
            date = Time.date('%Y-%m-%d')
            r1 = redis.delete('PROXY_STAT_TOL', [f"{date}*"])
            r2 = redis.delete('PROXY_STAT_FAL', [f"{date}*"])
            logger.warning(f"重置计数缓存 - {r1} - {r2} - {sk}", 'UP_DAY_CDL')
        # 快速转入批量队列中执行
        for c_list in chunk_list:
            RedisTaskQueue.add_task(sk, ','.join(c_list), is_force, current_date, vip)
        return True

    def update_symbol(self, code_str, is_force=0, current_date=None, vip=0):
        """
        更新股票基础数据

        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param int is_force: 是否强制更新
        :param str current_date: 当前日期 - %Y-%m-%d
        :param int vip: 是否使用特殊节点请求
        :return: 更新结果
        """
        sdb = GPLSymbolModel()
        code_list = code_str.split(',')
        if not code_list or vip < 0:
            return False
        all_code_list = self.formatter.get_stock_code_all()
        code_list = [self.formatter.sft.remove_stock_prefix(c) for c in code_list]
        symbol_list = [self.formatter.sft.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        s_list = {f"{d['symbol']}": d for d in s_list}

        def _up_sym_exec(code):
            res = {'td': current_date, 'ul': []}
            Time.sleep(Str.randint(1, 10) / 100)
            symbol = self.formatter.sft.add_stock_prefix(code)
            try:
                info = Attr.get(s_list, symbol)
                org_name = info.get('org_name') if info else 'None'
                percent = self.formatter.get_percent(code, code_list, all_code_list)
                logger.debug(f"更新股票数据<{symbol}>{percent} - {org_name}", 'UP_SYM_INF')
                if info and not is_force:
                    logger.warning(f"已存在股票数据跳过<{symbol}>", 'UP_SYM_SKP')
                    return False
                # 删除缓存
                if is_force and 6 > int(Time.date('%H')):
                    key_list = ['GPL_STOCK_INFO_XQ', 'GPL_STOCK_INFO_EM']
                    list(map(lambda key: redis.delete(key, [code]), key_list))
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

        [ _up_sym_exec(code) for code in code_list ]
        return True

    def update_symbol_daily(self, code_str, is_force=0, current_date=None, vip=1):
        """
        更新股票日线数据

        :param code_str: 股票代码列表，一般是50个
        :param is_force:  99: 仅拉取股票历史数据 | 98: 对历史数据入库 | 10: 今日 | 0,15: 更新最近五天  | 17: 最近一周
        :param str current_date: 当前日期 - %Y-%m-%d
        :param int vip: 是否使用特殊节点请求
        :return:
        """
        code_list = code_str.split(',')
        all_code_list = self.formatter.get_stock_code_all()
        code_list = [self.formatter.sft.remove_stock_prefix(c) for c in code_list]
        symbol_list = [self.formatter.sft.add_stock_prefix(c) for c in code_list]

        n = 5 if is_force == 0 else is_force - 10
        et = current_date if current_date else Time.date('%Y-%m-%d')
        st = Time.dnd(0 - n, et)
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

        def _up_day_exec(code):
            res = []
            symbol = self.formatter.sft.add_stock_prefix(code)
            percent = self.formatter.get_percent(code, code_list, all_code_list)
            insert_list = {}
            fq_list = {"": "0", "qfq": "1", "hfq": "2"}
            for k, v in fq_list.items():
                # 先判断是否已入库
                log_info = Attr.get(l_list[f'f{v}'], f"{symbol}_{tds}")
                if is_force == 99 and log_info:
                    logger.debug(f"日线数据已入库[{v}]<{symbol}><{tds}>{percent}", 'UP_DAY_SKP')
                    continue
                Time.sleep(Str.randint(5, 9) / 100)
                if log_info and is_force != 99:
                    day_list = log_info['process_params']
                else:
                    day_list = self.formatter.em.get_daily_quote(code, st, et, k, vip=vip)  # 内含Nat自动分流
                res.append(len(day_list))
                logger.debug(f"接口请求日线数据[{v}]<{symbol}><{tds}>{percent} - {k}"
                             f" - [{len(day_list)}]", 'UP_DAY_SKP')
                if not day_list:
                    logger.warning(f"暂无日线数据[{v}]<{symbol}><{tds}>{percent}", 'UP_DAY_WAR')
                    continue
                if 99 == is_force:
                    continue
                for i, day in enumerate(day_list):
                    td = day['date']
                    info = Attr.get(d_list, f"{symbol}_{td}")
                    day_data = {
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
                    }
                    if info:
                        if float(info[f"f{v}_close"]) <= 0:
                            if float(day['close']) <= 0:
                                logger.debug(f"接口日线数据为空[{v}]<{symbol}><{td}>{percent} - {day_data}", 'UP_DAY_SKP')
                            # 更新接口日线数据 - 之前的请求中可能没有正确得到数据
                            ddb.update_daily(info['id'], day_data)
                            logger.info(f"更新股票日线数据[{v}]<{symbol}><{td}>{percent} - {info['id']}", 'UP_DAY_FIX')
                        else:
                            if not i % 25 or is_force < 90:
                                logger.debug(f"已存在日线数据[{v}]<{symbol}><{td}>{percent}", 'UP_DAY_SKP')
                        continue
                    insert_list[td] = insert_list[td] if Attr.has_keys(insert_list, td) else {}
                    insert_list[td].update({
                        "symbol": symbol,
                        "trade_date": td,
                    } | day_data)
            if insert_list:
                ik = insert_list.keys()
                insert_list = insert_list.values()
                iid = ddb.add_daily(insert_list)
                res.append(iid)
                logger.debug(f"新增股票日线数据<{symbol}><{next(iter(ik))}~{next(reversed(ik))}>{percent}"
                             f" - END - {len(ik)} - {iid}", 'UP_DAY_INF')
            return res

        # 同步执行
        [ _up_day_exec(code) for code in code_list ]
        return True

        # 异步执行
        sleep_time = 10 if vip == 2 else 0
        return Sys.multy_thread(_up_day_exec, code_list, sleep_time=sleep_time)  # 分成多组同时执行

    def check_daily_data(self, code_str, is_force=0, current_date=None, vip=1):
        """检查日线数据是否完整"""
        current_date = current_date if is_force != 99 else self.formatter.INIT_ST  # 99 代表初始化
        current_date = current_date if current_date else Time.dnd(-63)  # 默认只检查最近三个月
        today = Time.dnd(-4)  # 留点间隙 - 普通日线每周同步一次
        ddb = GPLDailyModel()
        # cache_key = 'GPL_STOCK_CHECK_LIST'
        all_code_list = self.formatter.get_stock_code_all()
        code_list = code_str.split(',') if code_str else self.formatter.get_stock_code_all()
        td_list = self.formatter.get_td_list()

        def _check_day_exec(code):
            Time.sleep(Str.randint(5, 9) / 100)
            symbol = self.formatter.sft.add_stock_prefix(code)
            percent = self.formatter.get_percent(code, code_list, all_code_list)
            fq_list = {"": "0", "qfq": "1", "hfq": "2"}
            d_list = ddb.get_daily_list([symbol], [current_date, today])
            if not d_list:
                logger.warning(f"未查询到日线数据<{symbol}>[{current_date}]{percent}", 'CHK_DAY_WAR')
                return False
            d_list = {d['trade_date']: d for d in d_list}
            m_date = min(d_list.keys())
            for td in td_list:  # 检查每个交易日是否都有数据了
                if td < m_date or td > today:  # 小于第一条数据之前的日期就不管了
                    continue
                d = d_list.get(td)
                if not d:  # 连记录都没有
                    RedisTaskQueue.add_task('GPL_DAY', code, is_force, td, vip)
                    #redis.set(cache_key, {"d": td, "c": code, "t": f"{v}"}, [f"{str(td).replace('-', ':')}:{symbol}"])
                    logger.warning(f"交易日无日线数据<{symbol}>[{td}]{percent}", 'CHK_DAY_NON')
                    continue
                for k, v in fq_list.items():
                    if not d.get(f"f{v}_open") and not d.get(f"f{v}_close"):  # 有记录但是值为空
                        RedisTaskQueue.add_task('GPL_DAY', code, is_force, td, vip)
                        #redis.set(cache_key, {"d": td, "c": code, "t": f"{v}"}, [f"{str(td).replace('-', ':')}:{symbol}"])
                        logger.warning(f"交易日日线数据无效<{symbol}>[{td}]{percent} - {v} - {d['id']}", 'CHK_DAY_INV')
                        continue
            return True

        # 同步执行
        [ _check_day_exec(code) for code in code_list ]
        return True

    def clear_api_log(self):
        """清理api日志 - 保留10万条记录"""
        if True:
            return GplApiLogModel().clear_history() # 先用这个方式看看是否会超时，不行再用下面的方法
        r = 0
        save_count = 1000000
        ldb = GplApiLogModel()
        code_list = self.formatter.get_stock_code_all()
        count = 14097871 #ldb.get_count()
        mid = ldb.get_max_id()
        if mid <= save_count or count <= save_count or not code_list:
            return r
        for i, code in enumerate(code_list):
            symbol = self.formatter.sft.add_stock_prefix(code)
            percent = self.formatter.get_percent(code, code_list, code_list)
            r += ldb.delete({'id': {'opt': '<=', 'val': mid - save_count}, 'h_event': symbol})
            logger.info(f"删除接口日志数据[{i}/{r}]<{symbol}>{percent}", 'DEL_API_LOG')
        return r

