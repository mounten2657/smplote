from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_season_model import GPLSeasonModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateEgdService:
    """股票更新附属类 - 股东信息"""

    def __init__(self):
        self.formatter = GplFormatterService()

    def up_gd_em(self, symbol, gd_list, gd_list_free, day_list, n, is_special):
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

    def up_gdn_em(self, symbol, gdn_list, day_list, n, is_special):
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

    def up_gdt_em(self, symbol, gdt_list, day_list):
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

    def up_gdd_em(self, symbol, gdd_list, day_list):
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

    def up_gdl_em(self, symbol, gdd_list, day_list):
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
