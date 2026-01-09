from service.gpl.gpl_formatter_service import GplFormatterService
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from model.gpl.gpl_season_model import GPLSeasonModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateEdvService:
    """股票更新附属类 - 分红信息"""

    def __init__(self):
        self.formatter = GplFormatterService()

    def up_dvo_em(self, symbol, dvo_list, dvt_list, td):
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

    def up_dvh_em(self, symbol, dvh_list, td, n):
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
        for day in list(d_info.keys()):
            dv_info = Attr.get(dvh_list, f"{symbol}_{day}")
            if dv_info or day < self.formatter.INIT_ST:
                logger.warning(f"跳过分红历史数据<{symbol}><{day}>", 'UP_DVH_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入分红历史数据<{symbol}><{td}> - {len(d_info)}", 'UP_DVH_WAR')
        ret['idh'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def up_dvr_em(self, symbol, dvr_list, td, ed):
        """更新股票分红股息率 - 1000w数据"""
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
            if dv_info or day < self.formatter.INIT_ST:
                logger.warning(f"跳过分红股息率数据<{symbol}><{day}>", 'UP_DVR_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入分红股息率数据<{symbol}><{td}> - {len(d_info)}", 'UP_DVP_WAR')
        ret['idr'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def up_dvp_em(self, symbol, dvp_list, td, ed):
        """更新股票分红股利支付率"""
        # 只有每年的12月31才有数据，一二月份跑一下就行了
        if int(ed[5:7]) > 2:
            return {}
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
            if dv_info or day < self.formatter.INIT_ST:
                logger.warning(f"跳过分红股利支付率数据<{symbol}><{day}>", 'UP_DVP_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入分红股利支付率数据<{symbol}><{td}> - {len(d_info)}", 'UP_DVP_WAR')
        ret['idp'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def up_zyb_em(self, symbol, b_em):
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

    def up_zyi_em(self, symbol, zyi_list, is_all):
        """更新股票主营构成列表"""
        ret = {}
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '主营构成列表'
        biz_code = 'EM_ZY_IT'
        td_list = self.get_zyi_td_list(is_all)
        for t_list in td_list:
            sd, ed = t_list
            d_info = self.formatter.em.get_zy_item(symbol, sd, ed)
            if not d_info:
                logger.warning(f"暂无主营构成列表数据<{symbol}><{sd}/{ed}>", 'UP_ZYI_WAR')
                return ret
            for day in list(d_info.keys()):
                zy_info = Attr.get(zyi_list, f"{symbol}_{day}")
                if zy_info or day < self.formatter.INIT_ST:
                    logger.warning(f"跳过主营构成列表数据<{symbol}><{day}>", 'UP_ZYI_WAR')
                    del d_info[day]
                    continue
            logger.warning(f"批量插入主营构成列表数据<{symbol}><{sd}/{ed}> - {len(d_info)}", 'UP_ZYI_WAR')
            ret['izi'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def get_zyi_td_list(self, is_all):
        """获取主营构成的时间区间列表"""
        year = int(Time.date('%Y'))
        if is_all:
            return [['2000-01-01', '2010-01-01'], ['2010-01-01', '2020-01-01'], ['2020-01-01', '2030-01-01']]
        return [[f'{year - 1}-01-01', f'{year}-12-31']]

