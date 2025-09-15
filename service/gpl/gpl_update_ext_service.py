from service.gpl.gpl_formatter_service import GplFormatterService
from service.gpl.gpl_update_edv_service import GPLUpdateEdvService
from service.gpl.gpl_update_efn_service import GPLUpdateEfnService
from service.gpl.gpl_update_egd_service import GPLUpdateEgdService
from model.gpl.gpl_symbol_model import GPLSymbolModel
from model.gpl.gpl_const_kv_model import GPLConstKvModel
from model.gpl.gpl_concept_model import GPLConceptModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from model.gpl.gpl_season_model import GPLSeasonModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateExtService:
    """股票更新附属类"""

    # 初始化的开始结束日期
    _INIT_ST = GplFormatterService.INIT_ST
    _INIT_ET = GplFormatterService.INIT_ET

    # 无法正常获取股东信息的股票列表
    _S_GD_LIST = [
        "SH688755","SH603382","SZ301590","SH603014","SZ301636","SZ301662","SZ301678","SH688729","SZ301630","SH603262",
        "BJ920027", "BJ920037", "BJ920068", "BJ920108", "SH600930","SZ001400", "SZ301609"
    ]

    def __init__(self):
        self.formatter = GplFormatterService()
        self.edv = GPLUpdateEdvService()
        self.efn = GPLUpdateEfnService()
        self.egd = GPLUpdateEgdService()

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
        s_list = {f"{d['symbol']}": d for d in s_list}
        if not is_force:
            k_list_em = kdb.get_const_list('EM_CONCEPT')
            c_list_em = Attr.group_item_by_key(cdb.get_concept_list(symbol_list, 'EM'), 'symbol')
            t_list_em = Attr.group_item_by_key(tdb.get_text_list(symbol_list, 'EM_TC'), 'symbol')
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
        td = self._INIT_ET if is_all else Time.date('%Y-%m-%d')
        sd = self._INIT_ST if is_all else Time.dnd(td, -30)
        check_day = range(1, 32) if is_all else [1, 10, 20]
        if day in check_day:
            tdl = [] if is_all else day_list
            cdl = [Time.date('%Y-%m') + f"-{chd:02d}" for chd in check_day]
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
                dvh_list = jdb.get_season_list(symbol_list, [], 'EM_DV_HIST', sd)
            if 0 == is_force or 98 == is_force:
                dvr_list = jdb.get_season_list(symbol_list, [], 'EM_DV_HIST_R', sd)
            if 0 == is_force or 99 == is_force:
                dvp_list = jdb.get_season_list(symbol_list, [], 'EM_DV_HIST_P', sd)
            if 100 == is_force:
                b_list_em = Attr.group_item_by_key(tdb.get_text_list(symbol_list, 'EM_ZY_BA'), 'symbol')
            if 0 == is_force or 101 == is_force:
                zyi_list = jdb.get_season_list(symbol_list, [], 'EM_ZY_IT', sd)
            if 0 == is_force or 102 == is_force:
                fni_list = jdb.get_season_list(symbol_list, [], 'EM_FN_IT', sd)
            if 0 == is_force or 103 == is_force:
                fnd_list = jdb.get_season_list(symbol_list, [], 'EM_FN_DP', sd)
            if 0 == is_force or 104 == is_force:
                fnn_list = jdb.get_season_list(symbol_list, [], 'EM_FN_NF', sd)

        @Ins.multiple_executor(1)
        def _up_saf_exec(code):
            Time.sleep(Str.randint(1, 10) / 100)
            ret = {}
            symbol = Str.add_stock_prefix(code)
            info = Attr.get(s_list, symbol)
            percent = self.formatter.get_percent(code, code_list, all_code_list)
            if not info:
                logger.warning(f"未查询到股票数据<{symbol}>{percent}", 'UP_SAF_WAR')
                return False
            logger.debug(f"更新股票额外数据<{symbol}>{percent} - STA", 'UP_SAF_INF')
            # 季度相关数据
            if day in check_day:
                is_special = int(symbol in self._S_GD_LIST)
                sd_list = [Time.date('%Y-%m-%d') if not is_force else self._INIT_ET] if is_special else day_list
                # 东财十大股东更新
                if 0 == is_force or 91 == is_force:
                    ret = ret | self.egd.up_gd_em(symbol, gd_list, gd_list_free, sd_list, n, is_special)
                    logger.debug(f"更新十大股东结果<{symbol}>{percent} - GD - {ret}", 'UP_SAF_INF')
                # 东财股东人数合计更新
                if 0 == is_force or 92 == is_force:
                    ret = ret | self.egd.up_gdn_em(symbol, gdn_list, sd_list, n, is_special)
                    logger.debug(f"更新股东人数合计结果<{symbol}>{percent} - GN - {ret}", 'UP_SAF_INF')
                # 东财股东机构合计更新
                if 0 == is_force or 93 == is_force:
                    ret = ret | self.egd.up_gdt_em(symbol, gdt_list, day_list)
                    logger.debug(f"更新股东机构合计结果<{symbol}>{percent} - GT - {ret}", 'UP_SAF_INF')
                # 东财股东机构明细更新
                if 0 == is_force or 94 == is_force:
                    ret = ret | self.egd.up_gdd_em(symbol, gdd_list, day_list)
                    logger.debug(f"更新股东机构明细结果<{symbol}>{percent} - GA - {ret}", 'UP_SAF_INF')
                # 东财股东机构列表更新
                if 0 == is_force or 95 == is_force:
                    ret = ret | self.egd.up_gdl_em(symbol, gdl_list, day_list)
                    logger.debug(f"更新股东机构列表结果<{symbol}>{percent} - GL - {ret}", 'UP_SAF_INF')
                # 东财分红概览更新
                if 0 == is_force or 96 == is_force:
                    ret = ret | self.edv.up_dvo_em(symbol, dvo_list, dvt_list, td)
                    logger.debug(f"更新分红概览结果<{symbol}>{percent} - DO - {ret}", 'UP_SAF_INF')
                # 东财分红历史更新
                if 0 == is_force or 97 == is_force:
                    ret = ret | self.edv.up_dvh_em(symbol, dvh_list, td, n)
                    logger.debug(f"更新分红历史结果<{symbol}>{percent} - DH - {ret}", 'UP_SAF_INF')
                # 东财分红股息率更新
                if 0 == is_force or 98 == is_force:
                    ret = ret | self.edv.up_dvr_em(symbol, dvr_list, sd, td)
                    logger.debug(f"更新分红股息率结果<{symbol}>{percent} - DR - {ret}", 'UP_SAF_INF')
                # 东财分红股利支付率更新
                if 0 == is_force or 99 == is_force:
                    ret = ret | self.edv.up_dvp_em(symbol, dvp_list, sd, td)
                    logger.debug(f"更新分红股利支付率结果<{symbol}>{percent} - DP - {ret}", 'UP_SAF_INF')
                # 东财经营评述长文本更新
                if 100 == is_force:
                    b_em = Attr.get(b_list_em, symbol, [])
                    ret = ret | self.edv.up_zyb_em(symbol, b_em)
                    logger.debug(f"更新经营评述长文本结果<{symbol}>{percent} - ZYB - {ret}", 'UP_SAF_INF')
                # 东财主营构成列表更新
                if 0 == is_force or 101 == is_force:
                    year = int(Time.date('%Y'))
                    td_list = [[f'{year - 1}-01-01', f'{year}-12-31']]
                    if is_all:
                        td_list = [
                            ['2000-01-01', '2010-01-01'],
                            ['2010-01-01', '2020-01-01'],
                            ['2020-01-01', '2030-01-01'],
                        ]
                    ret = ret | self.edv.up_zyi_em(symbol, zyi_list, td_list)
                    logger.debug(f"更新主营构成列表结果<{symbol}>{percent} - ZYI - {ret}", 'UP_SAF_INF')
                # 东财财务主要指标更新
                if 0 == is_force or 102 == is_force:
                    ret = ret | self.efn.up_fni_em(symbol, fni_list, td, n)
                    logger.debug(f"更新财务主要指标结果<{symbol}>{percent} - FNI - {ret}", 'UP_SAF_INF')
                # 东财财务杜邦分析更新
                if 0 == is_force or 103 == is_force:
                    ret = ret | self.efn.up_fnd_em(symbol, fnd_list, td, n)
                    logger.debug(f"更新财务杜邦分析结果<{symbol}>{percent} - FND - {ret}", 'UP_SAF_INF')
                # 东财财务公告文件更新
                if 0 == is_force or 104 == is_force:
                    ret = ret | self.efn.up_fnn_em(symbol, fnn_list, td)
                    logger.debug(f"更新财务公告文件结果<{symbol}>{percent} - FNN - {ret}", 'UP_SAF_INF')
            if not is_force:
                cl_em = Attr.get(c_list_em, symbol, [])
                t_em = Attr.get(t_list_em, symbol, [])
                # 雪球概念更新
                if Time.date('%Y-%m-%d') <= self._INIT_ET:
                    cl_xq = Attr.get(c_list_xq, symbol, [])
                    ret = ret | self.formatter.update_by_xq(symbol, info, k_list_xq, cl_xq)
                    logger.debug(f"更新股票雪概结果<{symbol}>{percent} - XQ - {ret}", 'UP_SAF_INF')
                # 东财概念更新
                ret = ret | self.formatter.update_by_em(symbol, info, k_list_em, cl_em, t_em)
                logger.debug(f"更新股票东概结果<{symbol}>{percent} - EM - {ret}", 'UP_SAF_INF')
                # 变更日志更新
                ret = ret | self.formatter.update_change_log(symbol, info)
                logger.debug(f"更新股票变更结果<{symbol}>{percent} - CL - {ret}", 'UP_SAF_INF')
            return ret

        return _up_saf_exec(code_list)
