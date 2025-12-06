from service.gpl.gpl_formatter_service import GplFormatterService
from service.vpp.vpp_serve_service import VppServeService
from model.gpl.gpl_season_model import GPLSeasonModel
from model.gpl.gpl_file_model import GplFileModel
from model.gpl.gpl_symbol_text_model import GPLSymbolTextModel
from tool.core import Ins, Logger, Str, Time, Attr
from tool.unit.net.cache_http_client import CacheHttpClient

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
                    logger.warning(f"跳过财务公告文件数据<{symbol}><{day}><{dd['tid']}>", 'UP_SNF_WAR')
                    continue
                # 保存文本
                art_code = Attr.get(dd, 'art_code', '')
                fn_txt = self.formatter.em.get_fn_notice_txt(symbol, art_code)
                ps = fn_txt['page_size']
                content = fn_txt['content']
                # 有分页 - 需整合后再入库
                if ps > 1:
                    for ii in range(1, ps):
                        ft = self.formatter.em.get_fn_notice_txt(symbol, art_code, ii + 1)
                        if ft.get('content'):
                            content += ft['content']
                # 文本数据入库
                if fn_txt.get('content'):
                    tid = tdb.add_text({
                        "symbol": symbol,
                        "biz_code": biz_code,
                        "e_key": art_code,
                        "e_des": fn_txt['title'],
                        "e_val": str(content).strip(),
                    }, True)
                    if tid:
                        has_update = True
                        d['e_val'][i]['tid'] = tid
            if has_update:
                logger.warning(f"更新财务公告文本数据<{symbol}><{sd} ~ {td}> - <{i}/{len(dfl)}>", 'UP_SNF_WAR')
                ret['uft'][d['id']] = jdb.update_season(d['id'], {"e_val": d['e_val']})
        return ret

    def cache_fnn_em_txt(self, r_type=1, code_str=''):
        """
        缓存股票财务公告文本
          - 由于总数太多，正常一个个请求会需要很长地时间，故此通过代理池在短时间内完成大量网络请求并缓存
          - 已经入库的数据不用再去请求，注意过滤

        :param r_type: 执行次数：第一次统一请求第一页，全部完成后，再进行第二次，第二次根据第一次的结果再判断要请求几次分页数据
        :param code_str: 股票代码列表 - 多个用英文逗号隔开，为空默认全股票
        :return:
        """
        code_list = [Str.remove_stock_prefix(c) for c in code_str.split(',') if c.strip()]  # 有无前缀都去掉
        code_list = code_list if code_list else self.formatter.get_stock_code_all()  # 默认获取所有的股票代码列表
        jdb = GPLSeasonModel()
        tdb = GPLSymbolTextModel()
        biz_code = 'EM_FN_NT'
        par_list = []
        # 先统一整理数据，之后再作请求动作
        c_list = Attr.chunk_list(code_list, 50)  # 50个一组集中查询
        for cl in c_list:
            symbol_list = [Str.add_stock_prefix(c) for c in cl]
            symbol = symbol_list[0]
            percent = self.formatter.get_percent(cl[0], cl, code_list) + f" - {len(par_list)}"
            logger.info(f"获取财务公告文本数据缓存参数<{symbol}>{percent}", 'C_FNN_WAR')
            s_list = jdb.get_anr_code_list(symbol_list)  # 根据股票代码获取其下所有报告文件的代码
            if not s_list:
                continue
            t_list = tdb.get_text_list(symbol_list, biz_code, ['id', 'e_key'])  # 获取所有已保存的报告文件列表
            t_list = [t['e_key'] for t in t_list if t['e_key']]
            a_list = [s for s in s_list if s not in t_list]  # 只保留未获取过的数据
            if not a_list:
                continue
            for art_code in a_list:
                logger.debug(f"获取财务公告文本数据报告代码<{symbol}>{percent} - ({len(s_list)}/{len(t_list)}/{len(a_list)}) - {art_code}", 'C_FNN_DBG')
                par = self.formatter.em.get_fn_notice_txt_par(art_code, 1)
                a_cache = CacheHttpClient.get_req_cache(par['url'], par['params'])
                # {"data":{"art_code":"AN201606170015262533","attach_list":[{"attach_size":87,"attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","seq":1}],"attach_list_ch":[{"attach_size":87,"attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","seq":1}],"attach_list_en":[],"attach_size":"87","attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","attach_url_web":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","eitime":"2016-06-17 16:51:56","extend":{},"is_ai_summary":0,"is_rich":0,"is_rich2":0,"language":"0","notice_content":"证券代码：002030 证券简称：达安基因 公告编号：2016-045\r\n 中山大学达安基因股份有限公司\r\n 关于已授予股票期权注销完成的公告\r\n 本公司及董事会全体成员保证信息披露内容的真实、准确和完整，没有虚假记载、误导性陈述或重大遗漏。\r\n 中山大学达安基因股份有限公司（以下简称“公司”）第五届董事会第六次会议和第五届监事会第六次会议审议通过了《关于终止实施股票期权激励计划的预案》，并经2015年度股东大会审议通过，会议同意公司终止股票期权激励计划并注销已授予的股票期权。具体内容详见公司于2016年3月31日在《证券时报》、巨潮资讯网上刊登的《中山大学达安基因股份有限公司关于终止实施股票期权激励计划的公告》（公告编号：2016-011）。\r\n 经中国证券登记结算有限责任公司深圳分公司审核确认，公司已完成了对首期股票期权激励计划已授予的全部股票期权注销事宜，涉及激励对象67人，股票期权数量508.464万份。\r\n 特此公告。\r\n 中山大学达安基因股份有限公司\r\n 董事会\r\n 2016年6月17日\r\n","notice_date":"2016-06-18 00:00:00","notice_title":"达安基因:关于已授予股票期权注销完成的公告","page_size":1,"page_size_ch":0,"page_size_cht":0,"page_size_en":0,"security":[{"market_uni":"0","short_name":"达安基因","short_name_ch":"达安基因","short_name_cht":"達安基因","short_name_en":"DAJY","stock":"002030"}],"short_name":"达安基因"},"success":1}
                if 1 == r_type:  # 第一次请求
                    if a_cache:  # 有缓存的直接跳过
                        continue
                    par_list.append(par)
                else:  # 第二次请求
                    if not a_cache:
                        par_list.append(par)
                    else:
                        pn = Attr.get_by_point(a_cache, 'data.data.page_size', 0)
                        if not pn:  # 这种的应该是数据错误了，记个错误日志
                            logger.error(f"获取财务公告文本数据错误<{symbol}>{percent} - {pn} - {a_cache}", 'C_FNN_ERR')
                            continue
                        if 1== pn:  # 排除只有一页的数据，剩下的就都是多页的数据了
                            continue
                        for p in range(1, pn):
                            par_list.append(par | {"page_index": p + 1})
        # 已经获取到了所有参数，现在分为1000个一组，批量进行请求
        par_len = len(par_list)
        success = {"hpk": "data.notice_content"}  # 有具体内容才算成功
        par_list = Attr.chunk_list(par_list, 1000)
        for pl in par_list:
            CacheHttpClient.batch_request(pl, success)
            Time.sleep(1)  # 休眠一秒
        return par_len  # 返回数据总长度


