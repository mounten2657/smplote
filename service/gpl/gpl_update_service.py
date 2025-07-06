import concurrent
from concurrent.futures import ThreadPoolExecutor
from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.core import Ins, Logger, Str, Time, Attr, Error

logger = Logger()


@Ins.singleton
class GPLUpdateService:
    """股票更新类"""

    def __init__(self):
        self.formatter = GplFormatterService()

    def quick_update_symbol(self, code_str='', is_force=0):
        """
        多进程快速更新股票基础数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param is_force: 是否强制更新
        :return:
        """
        code_list = code_str.split(',') if code_str else self.formatter.get_stock_code_all()
        logger.warning(f"总股票数据 - {len(code_list)}", 'UP_SYM_TOL')
        if not code_list:
            return False
        chunk_list = Attr.chunk_list(code_list)
        # 先删除昨日相关概念板块
        if not code_str:
            cdb = GPLConceptModel()
            d_count = cdb.del_concept_yesterday('EM')
            logger.warning(f"删除昨日板块 - {d_count}", 'UP_SYM_YST')
        for c_list in chunk_list:
            i = int(sum(int(num) for num in c_list)) % 4 + 1
            RedisTaskQueue(f'rtq_gpl_sym{i}_queue').add_task('GPL_SYM', ','.join(c_list), is_force)
        return True

    def quick_update_symbol_ext(self, code_str=''):
        """
        多进程快速更新股票额外数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :return:
        """
        code_list = code_str.split(',') if code_str else self.formatter.get_stock_code_all()
        logger.warning(f"总股票数据 - {len(code_list)}", 'UP_SYM_TOL')
        if not code_list:
            return False
        chunk_list = Attr.chunk_list(code_list)
        for c_list in chunk_list:
            i = int(sum(int(num) for num in c_list)) % 4 + 1
            RedisTaskQueue(f'rtq_gpl_saf{i}_queue').add_task('GPL_SAF', ','.join(c_list))
        return True

    def update_symbol(self, code_str, is_force=0):
        """
        更新股票数据
        :param str code_str: 股票代码，不带市场前缀，多个用英文逗号隔开
        :param int is_force: 是否强制更新
        :return: 更新结果
        """
        res = {'un_ins_list': []}
        sdb = GPLSymbolModel()
        code_list = code_str.split(',')
        if not code_list:
            return False
        all_code_list = self.formatter.get_stock_code_all()
        symbol_list = [Str.add_stock_prefix(c) for c in code_list]
        s_list = sdb.get_symbol_list(symbol_list)
        for code in code_list:
            Time.sleep(Str.randint(1, 10) / 10)
            symbol = Str.add_stock_prefix(code)
            try:
                info = Attr.select_item_by_where(s_list, {"symbol": symbol})
                org_name = info.get('org_name') if info else 'None'
                ind = all_code_list.index(code) + 1
                percent = (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                           f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")
                logger.debug(f"更新股票数据<{symbol}>{percent} - {org_name}", 'UP_SYM_INF')
                if info and not is_force:
                    logger.warning(f"已存在股票数据跳过<{symbol}>", 'UP_SYM_SKP')
                    continue
                stock = self.formatter.get_stock_info(code, is_force)
                if not stock:
                    res['un_ins_list'].append(code)
                    logger.warning(f"未能更新的股票数据<{symbol}>", 'UP_SYM_WAR')
                    continue
                if not info:
                    # 新增
                    ext = {'update_list': {'cf': Time.date()}}
                    res['ins_sym'] = sdb.add_symbol(stock | ext)
                else:
                    # 更新
                    change_log = Attr.data_diff(Attr.select_keys(info, stock.keys()), stock)
                    if change_log:
                        before = Attr.select_keys(info, change_log.keys())
                        after = Attr.select_keys(stock, change_log.keys())
                        ext = {'update_list': info['update_list'] | {'uf': Time.date()}}
                        logger.warning(f"股票数据发生变化<{symbol}> - {change_log}", 'UP_SYM_WAR')
                        res['up_sym'] = sdb.update_symbol(symbol, after, before, ext)
            except Exception as e:
                res['un_ins_list'].append(code)
                err = Error.handle_exception_info(e)
                logger.error(f"更新股票数据出错<{symbol}> - {err}", 'UP_SYM_ERR')
                continue
        return res

    def update_symbol_ext(self, code_str):
        """更新股票额外数据 - 多线程"""
        res = {}
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

        def _up_saf_exec(code, ret):
            """更新方法入口"""
            symbol = Str.add_stock_prefix(code)
            info = Attr.select_item_by_where(s_list, {"symbol": symbol})
            ind = all_code_list.index(code) + 1
            percent = (f"[{ind}/{len(all_code_list)}]({round(100 * ind / len(all_code_list), 2)}% "
                       f"| {round(100 * (code_list.index(code) + 1) / len(code_list), 2)}%)")
            if not info:
                logger.warning(f"未查询到股票数据<{symbol}>{percent}", 'UP_SAF_WAR')
                return False
            cl_xq = Attr.get(c_list_xq, symbol, [])
            cl_em = Attr.get(c_list_em, symbol, [])
            t_em = Attr.get(t_list_em, symbol, [])
            # 雪球概念更新
            logger.debug(f"异步更新股票数据<{symbol}>{percent} - STA", 'UP_SAF_INF')
            ret = self.update_by_xq(symbol, info, ret, k_list_xq, cl_xq)
            # 东财概念更新
            logger.debug(f"异步更新股票结果<{symbol}>{percent} - XQ - {ret}", 'UP_SAF_INF')
            ret = self.update_by_em(symbol, info, ret, k_list_em, cl_em, t_em)
            logger.debug(f"异步更新股票结果<{symbol}>{percent} - EM - {ret}", 'UP_SAF_INF')
            return ret

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_code = {executor.submit(_up_saf_exec, code, res): code for code in code_list}
            res = {}
            for future in concurrent.futures.as_completed(future_to_code):
                Time.sleep(Str.randint(1, 10) / 10)
                code = future_to_code[future]
                try:
                    res[code] = future.result()
                except Exception as e:
                    err = Error.handle_exception_info(e)
                    res[code] = err

        return res

    def update_by_xq(self, symbol, info, res, k_list_xq, c_list_xq):
        """从雪球中拉取数据进行更新"""
        # 改为只更新一次 - 毕竟不常用
        if k_list_xq and c_list_xq:
            res['up_concept_xq'] = 'skip'
            return res
        code = info['code']
        stock = self.formatter.get_stock_info(code, 1)
        if stock:
            concept_code = Attr.get(stock, 'concept_code_xq', '')
            concept_name = Attr.get(stock, 'concept_name_xq', '')
            if concept_code and concept_name:
                res['up_concept_xq'] = self.update_concept(symbol, concept_code, concept_name, 'XQ', '', k_list_xq, c_list_xq)
        return res

    def update_by_em(self, symbol, info, res, k_list_em, c_list_em, t_em):
        """从东财中拉取数据进行更新"""
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
                    res['up_concept_em'] = self.update_concept(symbol, concept_code, concept_name, 'EM', des, k_list_em, c_list_em)
                    if '昨日' not in concept_name:
                        concept_list.append(concept_name)
            concept_list = ','.join(concept_list)
            if concept_list and info['concept_list'] != concept_list:
                before = Attr.select_keys(info, ['concept_list'])
                before = before if info['concept_list'] else {}
                ext = {'update_list': info['update_list'] | {'xq': Time.date()}}
                res['up_stock_em'] = sdb.update_symbol(symbol, {"concept_list": concept_list}, before, ext)
        # 核心题材
        ct_list = self.em.get_concept_text(code)
        if ct_list:
            biz_type = 'EM_TC'
            t_list = t_em
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
                    d_info = Attr.select_item_by_where(t_list, {'e_key': ek}, {})
                    if not d_info and not tdb.get_text(symbol, biz_type, ek):
                        res['ins_text_em'] = tdb.add_text({
                            "symbol": symbol,
                            "biz_type": biz_type,
                            "e_key": ek,
                            "e_des": title,
                            "e_val": c_text.strip(),
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
