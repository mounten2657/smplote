from service.gpl.gpl_formatter_service import GplFormatterService
from service.vpp.vpp_serve_service import VppServeService
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
    _INIT_ST = '2000-01-01'
    _INIT_ET = '2025-07-31'

    # 无法正常获取股东信息的股票列表
    _S_GD_LIST = [
        "SH688755","SH603382","SZ301590","SH603014","SZ301636","SZ301662","SZ301678","SH688729","SZ301630","SH603262",
        "BJ920027", "BJ920037", "BJ920068", "BJ920108", "SH600930","SZ001400", "SZ301609"
    ]

    def __init__(self):
        self.formatter = GplFormatterService()

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
                    ret = ret | self._up_dvr_em(symbol, dvr_list, sd, td)
                    logger.debug(f"更新分红股息率结果<{symbol}>{percent} - DR - {ret}", 'UP_SAF_INF')
                # 东财分红股利支付率更新
                if 0 == is_force or 99 == is_force:
                    ret = ret | self._up_dvp_em(symbol, dvp_list, sd, td)
                    logger.debug(f"更新分红股利支付率结果<{symbol}>{percent} - DP - {ret}", 'UP_SAF_INF')
                # 东财经营评述长文本更新
                if 100 == is_force:
                    b_em = Attr.get(b_list_em, symbol, [])
                    ret = ret | self._up_zyb_em(symbol, b_em)
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
                    ret = ret | self._up_zyi_em(symbol, zyi_list, td_list)
                    logger.debug(f"更新主营构成列表结果<{symbol}>{percent} - ZYI - {ret}", 'UP_SAF_INF')
                # 东财财务主要指标更新
                if 0 == is_force or 102 == is_force:
                    ret = ret | self._up_fni_em(symbol, fni_list, td, n)
                    logger.debug(f"更新财务主要指标结果<{symbol}>{percent} - FNI - {ret}", 'UP_SAF_INF')
                # 东财财务杜邦分析更新
                if 0 == is_force or 103 == is_force:
                    ret = ret | self._up_fnd_em(symbol, fnd_list, td, n)
                    logger.debug(f"更新财务杜邦分析结果<{symbol}>{percent} - FND - {ret}", 'UP_SAF_INF')
                # 东财财务公告文件更新
                if 0 == is_force or 104 == is_force:
                    ret = ret | self._up_fnn_em(symbol, fnn_list, td)
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

    def _up_zyb_em(self, symbol, b_em):
        """更新经营评述长文本"""
        ret = {}
        tdb = GPLSymbolTextModel()
        if b_em:
            logger.warning(f"跳过经营评述长文本数据<{symbol}>", 'UP_ZYB_WAR')
            return ret
        b_info = self.formatter.em.get_zy_ba_text(symbol)
        if not b_info:
            logger.warning(f"暂无经营评述长文本数据<{symbol}>", 'UP_ZYB_WAR')
            return ret
        ret['izb'] = tdb.add_text({
            "symbol": symbol,
            "biz_code": 'EM_ZY_BA',
            "e_key": 'jyps',
            "e_des": '经营评述',
            "e_val": b_info['ba_text'],
        })
        return ret

    def _up_zyi_em(self, symbol, zyi_list, td_list):
        """更新股票主营构成列表"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '主营构成列表'
        biz_code = 'EM_ZY_IT'
        for t_list in td_list:
            sd, ed = t_list
            d_info = self.formatter.em.get_zy_item(symbol, sd, ed)
            if not d_info:
                logger.warning(f"暂无主营构成列表数据<{symbol}><{sd}/{ed}>", 'UP_ZYI_WAR')
                return ret
            for day in list(d_info.keys()):
                zy_info = Attr.get(zyi_list, f"{symbol}_{day}")
                if zy_info or day < self._INIT_ST:
                    logger.warning(f"跳过主营构成列表数据<{symbol}><{day}>", 'UP_ZYI_WAR')
                    del d_info[day]
                    continue
            logger.warning(f"批量插入主营构成列表数据<{symbol}><{sd}/{ed}> - {len(d_info)}", 'UP_ZYI_WAR')
            ret['izi'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def _up_fni_em(self, symbol, fni_list, td, n):
        """更新股票财务主要指标"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '财务主要指标'
        biz_code = 'EM_FN_IT'
        d_info = self.formatter.em.get_fn_item(symbol, td, n)
        if not d_info:
            logger.warning(f"暂无财务主要指标数据<{symbol}><{td}> - {n}", 'UP_FNI_WAR')
            return ret
        for day in list(d_info.keys()):
            fi_info = Attr.get(fni_list, f"{symbol}_{day}")
            if fi_info or day < self._INIT_ST:
                logger.warning(f"跳过财务主要指标数据<{symbol}><{day}>", 'UP_FNI_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入财务主要指标数据<{symbol}><{td}> - {len(d_info)}", 'UP_FNI_WAR')
        ret['ifi'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def _up_fnd_em(self, symbol, fnd_list, td, n):
        """更新股票财务杜邦分析"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '财务杜邦分析'
        biz_code = 'EM_FN_DP'
        d_info = self.formatter.em.get_fn_dupont(symbol, td, n)
        if not d_info:
            logger.warning(f"暂无财务杜邦分析数据<{symbol}><{td}> - {n}", 'UP_FND_WAR')
            return ret
        for day in list(d_info.keys()):
            fd_info = Attr.get(fnd_list, f"{symbol}_{day}")
            if fd_info or day < self._INIT_ST:
                logger.warning(f"跳过财务杜邦分析数据<{symbol}><{day}>", 'UP_FND_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入财务杜邦分析数据<{symbol}><{td}> - {len(d_info)}", 'UP_FND_WAR')
        ret['ifd'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def _up_fnn_em(self, symbol, fnn_list, td):
        """更新股票财务公告文件"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '财务公告文件'
        biz_code = 'EM_FN_NF'

        def get_fn_file(pn, ps):
            d = self.formatter.em.get_fn_notice_file(symbol, td, pn, ps)
            t, d = Attr.get(d, "total"), Attr.get(d, "data")
            if not d or not t:
                logger.warning(f"暂无财务公告文件数据<{symbol}><{td}> - {pn}/{ps}", 'UP_FNF_WAR')
                return 0, {}
            return t, d

        def save_fn_file(d):
            res = {}
            if not d:
                return res
            for day in list(d.keys()):
                ff_info = Attr.get(fnn_list, f"{symbol}_{day}")
                date = day.replace('-', '')
                month = day[:8].replace('-', '')
                title = Attr.get(d[day], 'title', '')
                url = Attr.get(d[day], 'url', '')
                # 文件下载
                fn = f"{symbol}_{date}-{title}.pdf"
                fd = f"/gpl/notice_file/{symbol}/{month}/"
                d[day]['file_url'] = VppServeService.download_website_file(url, biz_code, fn, fd)
                if ff_info or day < self._INIT_ST:
                    logger.warning(f"跳过财务公告文件数据<{symbol}><{day}>", 'UP_FNF_WAR')
                    del d[day]
                    continue
            logger.warning(f"批量插入财务公告文件数据<{symbol}><{td}> - {len(d)}", 'UP_FNF_WAR')
            res['iff'] = jdb.add_season_list(symbol, biz_code, des, d)
            return res

        # 初次获取和处理
        total, d_info = get_fn_file(1, 50)
        ret[1] = save_fn_file(d_info)

        # 处理剩余分页数据
        for i in range(2, int(total/100) + 1):
            total, d_info = get_fn_file(i, 50)
            ret[i] = save_fn_file(d_info)

        return ret

