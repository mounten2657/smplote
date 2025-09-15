from service.gpl.gpl_formatter_service import GplFormatterService
from service.vpp.vpp_serve_service import VppServeService
from model.gpl.gpl_season_model import GPLSeasonModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateEfnService:
    """股票更新附属类 - 财务信息"""

    _INIT_ST = GplFormatterService.INIT_ST
    _INIT_ET = GplFormatterService.INIT_ET

    def __init__(self):
        self.formatter = GplFormatterService()

    def up_fni_em(self, symbol, fni_list, td, n):
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

    def up_fnd_em(self, symbol, fnd_list, td, n):
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

    def up_fnn_em(self, symbol, fnn_list, td):
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
