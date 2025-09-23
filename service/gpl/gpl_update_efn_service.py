from service.gpl.gpl_formatter_service import GplFormatterService
from service.vpp.vpp_serve_service import VppServeService
from model.gpl.gpl_season_model import GPLSeasonModel
from model.gpl.gpl_file_model import GplFileModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from tool.core import Ins, Logger, Str, Time, Attr

logger = Logger()


@Ins.singleton
class GPLUpdateEfnService:
    """股票更新附属类 - 财务信息"""

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
            if fi_info or day < self.formatter.INIT_ST:
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
            if fd_info or day < self.formatter.INIT_ST:
                logger.warning(f"跳过财务杜邦分析数据<{symbol}><{day}>", 'UP_FND_WAR')
                del d_info[day]
                continue
        logger.warning(f"批量插入财务杜邦分析数据<{symbol}><{td}> - {len(d_info)}", 'UP_FND_WAR')
        ret['ifd'] = jdb.add_season_list(symbol, biz_code, des, d_info)
        return ret

    def up_fnn_em(self, symbol, fnn_list, td, n):
        """更新股票财务公告文件"""
        d_list = []
        jdb = GPLSeasonModel()
        Time.sleep(Str.randint(1, 3) / 10)
        des = '财务公告文件'
        biz_code = 'EM_FN_NF'
        is_all = int(n > 50)
        n = 50 if is_all else n

        def get_fn_file(pn, ps):
            d = self.formatter.em.get_fn_notice_file(symbol, td, pn, ps)
            t, d = Attr.get(d, "total"), Attr.get(d, "data")
            if not d or not t:
                logger.warning(f"暂无财务公告文件数据<{symbol}><{td}> - {pn}/{ps}", 'UP_FNN_WAR')
                return 0, {}
            return t, d

        def save_fn_file(d):
            res = {}
            if not d:
                return res
            for day in list(d.keys()):
                ff_info = Attr.get(fnn_list, f"{symbol}_{day}")
                if ff_info or day < self.formatter.INIT_ST:
                    logger.warning(f"跳过财务公告文件数据<{symbol}><{day}>", 'UP_FNN_WAR')
                    del d[day]
                    continue
            logger.warning(f"批量插入财务公告文件数据<{symbol}><{td}> - {len(d)}", 'UP_FNN_WAR')
            res['iff'] = jdb.add_season_list(symbol, biz_code, des, d)
            return res

        # 初次获取和处理
        total, d_info = get_fn_file(1, n)
        d_list += d_info

        if is_all:
            # 处理剩余分页数据
            for i in range(2, int(total/100) + 1):
                total, d_info = get_fn_file(i, 50)
                d_list += d_info

        # 统一处理，避免分页拉取的数据不全
        d_list = Attr.group_item_by_key(d_list, 'date')
        return save_fn_file(d_list)

    def download_fnn_em(self, symbol, fnn_list, td, sd, info):
        """
        下载股票财务公告文件
          - 由于历史文件加起来至少占10T，空间不够，暂时只保留最近一个月的文件
        """
        dfl = []
        ret = {'uff': {}}
        jdb = GPLSeasonModel()
        biz_code = 'EM_FN_NF'
        if symbol:  # 直接覆原始原日期，强制变成一个月
            td = Time.date('%Y-%m-%d')
            sd = Time.dnd(td, -30)
        date_list = Time.generate_date_list(sd, td)

        for d in date_list:
            dfi = Attr.get(fnn_list, f"{symbol}_{d}")
            if dfi:
                dfl.append(dfi)
        if not dfl:
            logger.warning(f"暂无财务公告文件数据<{symbol}><{sd} ~ {td}>", 'UP_DFN_WAR')
            return {}

        for d in dfl:
            day = d['season_date']
            date = day.replace('-', '')
            month = day[:8].replace('-', '')
            has_update = False
            for i in range(0, len(d['e_val'])):
                dd = d['e_val'][i]
                if dd.get('file_md5') or day < self.formatter.INIT_ST:
                    logger.warning(f"跳过财务公告文件数据<{symbol}><{day}><{dd['file_md5']}>", 'UP_DFN_WAR')
                    continue
                # 文件下载
                Time.sleep(Str.randint(1, 5) / 10)
                title = Attr.get(dd, 'title', '')
                url = Attr.get(dd, 'url', '')
                fn = Str.filter_target_chars(f"{symbol}_{date}-{title}.pdf")
                fd = f"/gpl/notice_file/{symbol}/{month}/"
                file = VppServeService.download_website_file(url, biz_code, fn, fd, 5002)
                # 文件数据入库
                f_info = {}
                if file.get('url'):
                    fdb = GplFileModel()
                    f_info = fdb.get_gpl_file(file['md5'])
                    if not f_info:
                        fdb.add_gpl_file(file | {
                            "symbol": symbol,
                            "symbol_name": info.get('org_name', symbol),
                            "season_date": td,
                            "biz_code": biz_code,
                        })
                        f_info = fdb.get_gpl_file(file['md5'])
                if f_info:
                    # 将本地文件信息存入数据库
                    d['e_val'][i]['file_md5'] = f_info.get('file_md5')
                    d['e_val'][i]['file_path'] = f_info.get('save_path')
                    d['e_val'][i]['file_url'] = f_info.get('url')
                    has_update = True
            if has_update:
                logger.warning(f"更新财务公告文件数据<{symbol}><{sd} ~ {td}> - <{i}/{len(dfl)}>", 'UP_DFN_WAR')
                ret['uff'][d['id']] = jdb.update_season(d['id'], {"e_val": d['e_val']})
        return ret

    def save_fnn_em_txt(self, symbol, fnn_list, td, sd):
        """
        保存股票财务公告文本
          - 由于历史文件加起来占的空间太大，所以以文本方式入库代替
        """
        dfl = []
        ret = {'uft': {}}
        jdb = GPLSeasonModel()
        tdb = GPLSymbolTextModel()
        biz_code = 'EM_FN_NT'
        date_list = Time.generate_date_list(sd, td)

        for d in date_list:
            dfi = Attr.get(fnn_list, f"{symbol}_{d}")
            if dfi:
                dfl.append(dfi)
        if not dfl:
            logger.warning(f"暂无财务公告文本数据<{symbol}><{sd} ~ {td}>", 'UP_SFN_WAR')
            return {}

        for d in dfl:
            day = d['season_date']
            has_update = False
            for i in range(0, len(d['e_val'])):
                dd = d['e_val'][i]
                if dd.get('tid') or day < self.formatter.INIT_ST:
                    logger.warning(f"跳过财务公告文件数据<{symbol}><{day}><{dd['file_md5']}>", 'UP_SNF_WAR')
                    continue
                # 保存文本
                art_code = Attr.get(dd, 'art_code', '')
                fn_txt = self.formatter.em.get_fn_notice_txt(symbol, art_code)
                ps = fn_txt['page_size']
                content = fn_txt['content']
                # 有分页 - 需整合后再入库
                if ps > 1:
                    for i in range(1, ps):
                        ft = self.formatter.em.get_fn_notice_txt(symbol, art_code, i + 1)
                        if ft.get('content'):
                            content += ft['content']
                # 文本数据入库
                if fn_txt.get('content'):
                    tid = tdb.add_text({
                        "symbol": symbol,
                        "biz_code": biz_code,
                        "e_key": art_code,
                        "e_des": fn_txt['title'],
                        "e_val": content,
                    })
                    if tid:
                        has_update = True
                        d['e_val'][i]['tid'] = tid
            if has_update:
                logger.warning(f"更新财务公告文本数据<{symbol}><{sd} ~ {td}> - <{i}/{len(dfl)}>", 'UP_SNF_WAR')
                ret['uft'][d['id']] = jdb.update_season(d['id'], {"e_val": d['e_val']})
        return ret
