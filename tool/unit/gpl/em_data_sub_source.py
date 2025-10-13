from typing import Dict, List
from tool.core import Logger, Attr, Time, Http, Dir, File
from tool.unit.gpl.em_data_formatter import EmDataFormatter
from tool.unit.gpl.em_data_source import EmDataSource

logger = Logger()


class EmDataSubSource(EmDataSource):
    """东方财富数据源子类"""

    def get_dv_ov(self, stock_code: str, sd: str) -> List:
        """
        获取股票分红概览

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :return: 股票分红概览
        {"dv_num": 13, "dv_money": 145240366.64, "raise_num": 1, "raise_money": 715700000, "dv_fn_rate": 20.293470258499998, "dv_pay_rate": 0, "dv_rate": 0}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_DIVIDENDNEW_PROFILE",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
        }
        data, pid = self._get(url, params, 'EM_DV_OV', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'dv_num': Attr.get(d, 'DIVIDEND_NUM', 0),  # 分红次数
            'dv_money': Attr.get(d, 'TOTAL_DIVIDEND', 0.0),  # 分红金额
            'raise_num': Attr.get(d, 'TOTAL_NUM', 0),  # 融资次数
            'raise_money': Attr.get(d, 'TOTAL_RAISE_FUND', 0.0),  # 融资金额
            'dv_fn_rate': Attr.get(d, 'DIVIDEND_FINANCE_RATIO', 0.0) * 100,  # 派现融资比
            'dv_pay_rate': Attr.get(d, 'DIVIDEND_PAY_RATIO', 0.0) * 100,  # 股利支付率
            'dv_rate': Attr.get(d, 'DIVIDEND_RATIO', 0.0) * 100,  # 股息率
        } for d in res]
        return self._ret(ret[0] if ret else {}, pid, start_time)

    def get_dv_ov_text(self, stock_code: str, sd: str) -> List:
        """
        获取股票分红概览描述

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :return: 股票分红概览描述
        {"dv_lv": "中", "dv_text": "1、2025一季报基本每股收益0元\n2、2025一季报每股未分配利润0.8358元\n3、2024年报每股股利无\n4、2024中报未分红\n5、近5年派现4次", "per_netcash_operate": -0.084702756733, "per_unassign_profit": 0.835833448547}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_DIVIDENDNEW_LITY",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
        }
        data, pid = self._get(url, params, 'EM_DV_OV_TEXT', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'dv_lv': Attr.get(d, 'DIVIDEND_LEVEL', ''),  # 潜在派现概率: 小 | 中 | 大
            'dv_text': Attr.get(d, 'PUBLISH_INFO', ''),  # 派现原因描述
            'per_netcash_operate': Attr.get(d, 'PER_NETCASH_OPERATE', 0.0),  # 每笔归母净利润
            'per_unassign_profit': Attr.get(d, 'PER_UNASSIGN_PROFIT', 0.0),  # 每笔未分配利润
        } for d in res]
        return self._ret(ret[0] if ret else {}, pid, start_time)

    def get_dv_hist(self, stock_code: str, sd: str, limit: int = 3) -> List:
        """
        获取股票分红历史列表

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int limit: 返回条数
        :return: 股票分红历史列表
        [{"date": "2025-04-18", "dv_rpn": "2024年报", "dv_obj": "", "dv_prg": "股东大会预案", "dv_plan": "不分配不转增", "record_date": "", "ex_date": "", "pay_date": "", "dv_money": 0}, {"date": "2024-08-24", "dv_rpn": "2024半年报", "dv_obj": "", "dv_prg": "董事会预案", "dv_plan": "不分配不转增", "record_date": "", "ex_date": "", "pay_date": "", "dv_money": 0}, {"date": "2024-07-03", "dv_rpn": "2023年报", "dv_obj": "全体股东", "dv_prg": "实施方案", "dv_plan": "10派0.1元", "record_date": "2024-07-10", "ex_date": "2024-07-11", "pay_date": "2024-07-11", "dv_money": 2989576}]
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_DIVIDEND_MAIN",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
            "pageNumber": 1,
            "pageSize": limit,
            "sortColumns": "NOTICE_DATE",
        }
        data, pid = self._get(url, params, 'EM_DV_HIST', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{limit}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['NOTICE_DATE'][:10],  # 公告日期
            'dv_rpn': Attr.get(d, 'REPORT_DATE', ''),  # 报告期
            'dv_obj': Attr.get(d, 'ASSIGN_OBJECT', ''),  # 分配对象： 全体股东 | ''
            'dv_prg': Attr.get(d, 'ASSIGN_PROGRESS', ''),  # 方案进度:： 实施方案 | 董事会预案 | 股东大会预案
            'dv_plan': Attr.get(d, 'IMPL_PLAN_PROFILE', ''),  # 分红方案
            'record_date': d['EQUITY_RECORD_DATE'][:10] if d['EQUITY_RECORD_DATE'] else '',  # 股权登记日
            'ex_date': d['EX_DIVIDEND_DATE'][:10] if d['EX_DIVIDEND_DATE'] else '',  # 除权除息日
            'pay_date': d['PAY_CASH_DATE'][:10] if d['PAY_CASH_DATE'] else '',  # 派息日
            'dv_money': Attr.get(d, 'TOTAL_DIVIDEND', 0.0),  # 分红金额
        } for d in res]
        ret = Attr.group_item_by_key(reversed(ret), 'date')
        return self._ret(ret if ret else {}, pid, start_time)

    def get_dv_hist_rate(self, stock_code: str, sd: str, ed: str) -> List:
        """
        获取股票分红历史股息率列表
          - [!] 1000w数据，考虑迁移或精简或丢弃

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2021-03-31）
        :param str ed: 结束日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :return: 股票分红历史股息率列表
        {"2015-07-31": {"date": "2015-07-31", "dv_rate": 0.1224289912, "dv_7d_hyy": -0.94192173093, "dv_7d_ttb": 2.108, "is_ex_date": 0}}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_DIVIDEND_CURVE",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")(TRADE_DATE>=\'{sd}\')',
            "pageNumber": 1,
            "sortColumns": "TRADE_DATE",
        }
        data, pid = self._get(url, params, 'EM_DV_HIST_R', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{ed}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['TRADE_DATE'][:10],  # 日期
            'dv_rate': Attr.get(d, 'DIVIDEND_RATIO_HYY', 0.0),  # 股息率
            'dv_7d_hyy': Attr.get(d, 'DIVIDEND_7DAYS', 0.0),  # 七日年化收益率 - HYY
            'dv_7d_ttb': Attr.get(d, 'YIELD_7DAYS', 0.0),  # 七日年化收益率 - 天天宝
            'is_ex_date': int(Attr.get(d, 'IS_EX_DIVIDEND_DATE', '0')),  # 是否除权日
        } for d in res]
        ret = Attr.group_item_by_key(ret, 'date')
        ret = {k: ret[k][0] for k in sorted(ret.keys())}
        return self._ret(ret if ret else {}, pid, start_time)

    def get_dv_hist_pay_rate(self, stock_code: str, sd: str, ed: str) -> List:
        """
        获取股票分红历史股利支付率列表

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2021-03-31）
        :param str ed: 结束日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :return: 股票分红历史股利支付率列表
        {"2007-12-31": {"date": "2007-12-31", "dv_imp": 0.0, "dv_pft": 19951320.29, "dv_pay_rate": 0}}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_DIVIDEND_HISTOGRAM",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")(REPORT_DATE>=\'{sd}\')',
            "pageNumber": 1,
            "sortColumns": "REPORT_DATE",
        }
        data, pid = self._get(url, params, 'EM_DV_HIST_P', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{ed}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],  # 日期
            'dv_imp': Attr.get(d, 'DIVIDEND_IMPLE', 0.0),  # 归母净利润
            'dv_pft': Attr.get(d, 'PARENTNETPROFIT', 0.0),  # 派现总额
            'dv_pay_rate': Attr.get(d, 'DIVIDEND_PAY_IMPLE', 0.0),  # 股利支付率
        } for d in res]
        ret = Attr.group_item_by_key(ret, 'date')
        ret = {k: ret[k][0] for k in sorted(ret.keys())}
        return self._ret(ret if ret else {}, pid, start_time)

    def get_zy_ba_text(self, stock_code: str) -> List:
        """
        获取股票经营评述长文本

        :param str stock_code: 股票代码，如： 002107
        :return: 股票经营评述长文本
        {"date": "2007-12-31", "ba_text": "xxx"}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_OP_BUSINESSANALYSIS",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
            "pageNumber": 1,
            "pageSize": 1,
        }
        data, pid = self._get(url, params, 'EM_ZY_BA', {'he': f'{prefix}{stock_code}', 'hv': f"{Time.date('%Y-%m-%d')}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],  # 日期
            'ba_text': Attr.get(d, 'BUSINESS_REVIEW', ''),  # 长文本
        } for d in res]
        return self._ret(ret[0] if ret else {}, pid, start_time)

    def get_zy_item(self, stock_code: str, sd: str, ed: str) -> List:
        """
        获取股票主营构成列表

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 开始日期 - Y-m-d（如： 2025-03-31）
        :param str ed: 结束日期 - Y-m-d（如： 2025-03-31）
        :return: 股票主营构成列表
        {"2024-12-31": [{"date": "2024-12-31", "zy_name": "电动工具行业", "zy_type": "1", "zy_income": 432748326.37, "zy_i_rate": 98.9861, "zy_cost": 377624303.29, "zy_c_rate": 99.995, "zy_profit": 55124023.08, "zy_p_rate": 92.5867, "zy_m_rate": 12.7381}]}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        is_all_str = f"(REPORT_DATE>='{sd}')(REPORT_DATE<='{ed}')"
        params = {
            "reportName": "RPT_F10_FN_MAINOP",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}"){is_all_str}',
            "pageNumber": 1,
            "pageSize": 100,
            "sortTypes": '1,1',
            "sortColumns": 'MAINOP_TYPE,RANK',
        }
        data, pid = self._get(url, params, 'EM_ZY_IT', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{ed}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],
            'zy_name': Attr.get(d, 'ITEM_NAME', ''),  # 主营业务名称名称
            'zy_type': Attr.get(d, 'MAINOP_TYPE', ''),  # 主营业务分类： 1:按行业分类 | 2:按产品分类 | 3:按地区分类
            'zy_income': Attr.get(d, 'MAIN_BUSINESS_INCOME', 0),  # 主营收入
            'zy_i_rate': Attr.get(d, 'MBI_RATIO', 0.0) * 100,  # 主营收入占比
            'zy_cost': Attr.get(d, 'MAIN_BUSINESS_COST', 0.0),  # 主营成本
            'zy_c_rate': Attr.get(d, 'MBC_RATIO', 0.0) * 100,  # 主营成本占比
            'zy_profit': Attr.get(d, 'MAIN_BUSINESS_RPOFIT', 0.0),  # 主营利润
            'zy_p_rate': Attr.get(d, 'MBR_RATIO', 0.0) * 100,  # 主营利润占比
            'zy_m_rate': Attr.get(d, 'GROSS_RPOFIT_RATIO', 0.0) * 100,  # 毛利率
        } for d in res]
        ret = Attr.group_item_by_key(ret, 'date')
        ret = {k: ret[k] for k in sorted(ret.keys())}
        return self._ret(ret, pid, start_time)

    def get_news_summary(self, stock_code: str, sd: str, pn=1, ps=50) -> Dict:
        """
        获取股票资讯摘要 - [!][弃用中]
          - [!] 报错 400 Client Error: Bad Request for url: xxx - 暂时保留，等后面有需要再研究
          - https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=SZ300126&color=b#/zxgg

        :param str stock_code: 股票代码，如： 002107
         :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int pn: 页码
        :param int ps: 条数
        :return: 股票资讯摘要
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._NEWS_URL + "/infoService"
        params = {
            "args": {
                "fields": 'code,infoCode,title,showDateTime,summary,uniqueUrl,url',
                "market": prefix_int,
                "pageNumber": pn,
                "pageSize": ps,
                "securityCode": f'{stock_code}',
            },
            "method": 'securityNews',
        }
        data, pid = self._get(url, params, 'EM_NEWS_SUM', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{pn},{ps}"}, 'POST')
        print(data)
        res = Attr.get_by_point(data, 'data.items', [])
        ret = [{
            'date': Time.dft(int(d['showDateTime']/1000), '%Y-%m-%d'),
            'code': Attr.get(d, 'code', ''),  # 新闻代码
            'title': Attr.get(d, 'title', ''),  # 新闻标题
            'summary': Attr.get(d, 'summary', ''),  # 新闻摘要
            'post_time': d['showDateTime'],  # 发布时间: int - 毫秒时间戳
            'url': f"https://finance.eastmoney.com/a/{Attr.get(d, 'code', '')}.html",  # 新闻链接
            # 'url': d['uniqueUrl'],  # 新闻链接
        } for d in res]
        return self._ret(ret, pid, start_time)

    def get_fn_item(self, stock_code: str, sd: str, limit=0) -> Dict:
        """
        获取股票财务主要指标

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int limit: 返回条数
        :return: 股票财务主要指标
        {"2024-12-31": {"date": "2024-12-31", "notice_date": "2025-04-18", "p_eps_jb": -0.06, "p_eps_jb_tz": -700, "p_eps_kc_jb": -0.14, "p_eps_xs": -0.06, "p_eps": 0.0, "p_gjj": 1.557273888003, "p_wfp": 0.834053867151, "p_xjl": -0.11674343869, "g_ys": 437180991.31, "g_ys_tz": -12.7698634397, "g_ys_hz": 4.199284146864, "g_mlr": 59537731.35, "g_gs_jlr": -19264406.98, "g_gs_jlr_tz": -575.1947648102, "g_gs_jlr_hz": -9.202684435737, "g_kf_jlr": -40881517.23, "g_kf_jlr_tz": -846.5214359214, "g_kf_jlr_hz": -18.248316865292, "m_jzc_syl": -1.8, "m_jzc_syl_kf": -3.82, "m_zzc_syl": -1.4686473548, "m_zzc_syl_tz": -584.1361558687, "m_mll": 13.618554450777, "m_jll": -4.4066134445, "q_ys_ys": 0.0, "q_xs_ys": 0.151679403629, "q_jy_ys": -0.081167882743, "q_tax": 0.0, "r_ld": 3.8722411308, "r_sd": 3.202276652421, "r_xj_ll": -0.16759009139, "r_zc_fz": 17.1472528868, "r_qy": 1.206960583496, "r_cq": 0.206960583496, "y_zz_ts": 1080.16457109263, "y_ch_ts": 144.719955940419, "y_ys_ts": 64.367103163103, "y_zz_bl": 0.333282547525, "y_ch_bl": 2.487562946386, "y_ys_bl": 5.59291908924}}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/get"
        limit = limit if limit else 3
        params = {
            "type": "RPT_F10_FINANCE_MAINFINADATA",
            "sty": "APP_F10_MAINFINADATA",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
            "p": 1,
            "ps": limit,
            "sr": '-1',
            "st": 'REPORT_DATE',
        }
        data, pid = self._get(url, params, 'EM_FN_IT', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{limit}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],
            'notice_date': d['NOTICE_DATE'][:10],  # 公示日期
            # 每股指标
            'p_eps_jb': Attr.get(d, 'EPSJB', 0.0),  # 基本每股收益(元)
            'p_eps_jb_tz': Attr.get(d, 'EPSJBTZ', 0.0),  # 每股收益同比增长(%)
            'p_eps_kc_jb': Attr.get(d, 'EPSKCJB', 0.0),  # 扣非每股收益(元)
            'p_eps_xs': Attr.get(d, 'EPSXS', 0.0),  # 稀释每股收益(元)
            'p_eps': Attr.get(d, 'EPS', 0.0),  # 每股净资产(元)
            'p_gjj': Attr.get(d, 'MGZBGJ', 0.0),  # 每股公积金(元)
            'p_wfp': Attr.get(d, 'MGWFPLR', 0.0),  # 每股未分配利润(元)
            'p_xjl': Attr.get(d, 'MGJYXJJE', 0.0),  # 每股经营现金流(元)
            # 成长指标
            'g_ys': Attr.get(d, 'TOTALOPERATEREVE', 0.0),  # 营业总收入(元)
            'g_ys_tz': Attr.get(d, 'TOTALOPERATEREVETZ', 0.0),  # 营业总收入同比增长(%)
            'g_ys_hz': Attr.get(d, 'YYZSRGDHBZC', 0.0),  # 营业总收入滚动环比增长(%)
            'g_mlr': Attr.get(d, 'MLR', 0.0),  # 毛利润(元)
            'g_gs_jlr': Attr.get(d, 'PARENTNETPROFIT', 0.0),  # 归属净利润(元)
            'g_gs_jlr_tz': Attr.get(d, 'PARENTNETPROFITTZ', 0.0),  # 归属净利润同比增长(%)
            'g_gs_jlr_hz': Attr.get(d, 'NETPROFITRPHBZC', 0.0),  # 归属净利润滚动环比增长(%)
            'g_kf_jlr': Attr.get(d, 'KCFJCXSYJLR', 0.0),  # 扣非净利润(元)
            'g_kf_jlr_tz': Attr.get(d, 'KCFJCXSYJLRTZ', 0.0),  # 扣非净利润同比增长(%)
            'g_kf_jlr_hz': Attr.get(d, 'KFJLRGDHBZC', 0.0),  # 扣非净利润滚动环比增长(%)
            # 盈利指标
            'm_jzc_syl': Attr.get(d, 'ROEJQ', 0.0),  # 净资产收益率(加权)(%)
            'm_jzc_syl_kf': Attr.get(d, 'ROEKCJQ', 0.0),  # 净资产收益率(扣非/加权)(%)
            'm_zzc_syl': Attr.get(d, 'ZZCJLL', 0.0),  # 总资产收益率(加权)(%)
            'm_zzc_syl_tz': Attr.get(d, 'ZZCJLLTZ', 0.0),  # 总资产收益率(加权)同比增长(%)
            'm_mll': Attr.get(d, 'XSMLL', 0.0),  # 毛利率(%)
            'm_jll': Attr.get(d, 'XSJLL', 0.0),  # 净利率(%)
            # 收益质量指标
            'q_ys_ys': Attr.get(d, 'YSZKYYSR', 0.0),  # 预收账款/营业收入
            'q_xs_ys': Attr.get(d, 'XSJXLYYSR', 0.0),  # 销售净现金流/营业收入
            'q_jy_ys': Attr.get(d, 'JYXJLYYSR', 0.0),  # 经营净现金流/营业收入
            'q_tax': Attr.get(d, 'TAXRATE', 0.0),  # 实际税率(%)
            # 财务风险指标
            'r_ld': Attr.get(d, 'LD', 0.0),  # 流动比率(%)
            'r_sd': Attr.get(d, 'SD', 0.0),  # 速动比率(%)
            'r_xj_ll': Attr.get(d, 'XJLLB', 0.0),  # 现金流量比率(%)
            'r_zc_fz': Attr.get(d, 'ZCFZL', 0.0),  # 资产负债率(%)
            'r_qy': Attr.get(d, 'QYCS', 0.0),  # 权益系数
            'r_cq': Attr.get(d, 'CQBL', 0.0),  # 产权比率(%)
            # 营运能力指标
            'y_zz_ts': Attr.get(d, 'ZZCZZTS', 0.0),  # 总资产周转天数(天)
            'y_zz_bl': Attr.get(d, 'TOAZZL', 0.0),  # 总资产周转率(次)
            'y_ch_ts': Attr.get(d, 'CHZZTS', 0.0),  # 存货周转天数(天)
            'y_ch_bl': Attr.get(d, 'CHZZL', 0.0),  # 存货周转率(次)
            'y_ys_ts': Attr.get(d, 'YSZKZZTS', 0.0),  # 应收账款周转天数(天)
            'y_ys_bl': Attr.get(d, 'YSZKZZL', 0.0),  # 应收账款周转率(次)
        } for d in res]
        ret = Attr.group_item_by_key(ret, 'date')
        ret = {k: ret[k][0] for k in sorted(ret.keys())}
        return self._ret(ret, pid, start_time)

    def get_fn_dupont(self, stock_code: str, sd: str, limit=0) -> Dict:
        """
        获取股票财务杜邦分析

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int limit: 返回条数
        :return: 股票财务杜邦分析
        {"2024-12-31": {"date": "2024-12-31", "notice_date": "2025-04-18", "data": {"roe_jq": {"des": "净资产收益率(加权)(%)", "val": -1.8, "sub": []}, "roe": {"des": "净资产收益率(%)", "val": -1.772599468299265, "sub": [{"des": "总资产净利率(%)", "val": -1.4686473548, "sub": [{"des": "营业净利润率(%)", "val": -4.406613444531, "sub": [{"des": "净利润(元)", "val": -19264876.34, "sub": [{"des": "收入总额(元)", "val": 471996334.81, "sub": [{"des": "营业总收入(元)", "val": 437180991.31, "sub": []}, {"des": "投资收益(元)", "val": 16427976.08, "sub": []}, {"des": "公允价值变动收益(元)", "val": 9723099.92, "sub": []}, {"des": "资产处置收益(元)", "val": 401192.39, "sub": []}, {"des": "汇兑收益(元)", "val": 0.0, "sub": []}]}, {"des": "成本总额(元)", "val": 478070639.51, "sub": [{"des": "营业成本(元)", "val": 377643259.96, "sub": []}, {"des": "税金及附加(元)", "val": 4894667.04, "sub": []}, {"des": "所得 税费用(元)", "val": 1097657.52, "sub": []}, {"des": "资产减值损失(元)", "val": -4613120.55, "sub": []}, {"des": "信用减值损失(元)", "val": -1361188.97, "sub": []}, {"des": "营业外 支出(元)", "val": 1241952.6, "sub": []}, {"des": "期间费用(元)", "val": 100409364.51, "sub": [{"des": "财务费用(元)", "val": -774219.63, "sub": []}, {"des": "销售费用(元)", "val": 37875442.17, "sub": []}, {"des": "管理费用(元)", "val": 0.0, "sub": []}, {"des": "研发费用(元)", "val": 28149784.35, "sub": []}]}]}]}, {"des": "营业总收入(元)", "val": 437180991.31, "sub": []}]}, {"des": "总资产周转率(次)", "val": 0.333282547525, "sub": []}]}, {"des": "归属母公司股东的净利润占比(%)", "val": 99.997563649038, "sub": []}, {"des": "权益乘数", "val": 1.206960583496, "sub": [{"des": "资产负债率(%)", "val": 17.147252886787, "sub": [{"des": "负债总额(元)", "val": 218779235.24, "sub": []}, {"des": "资产总额(元)", "val": 1275885045.17, "sub": [{"des": "流动资产(元)", "val": 819897465.68, "sub": [{"des": "货币资金(元)", "val": 128867415.11, "sub": []}, {"des": "交易性金融资产(元)", "val": 0.0, "sub": []}, {"des": "应收票据(元)", "val": 8814657.12, "sub": []}, {"des": "应收账款(元)", "val": 73887523.41, "sub": []}, {"des": "应收账款融资(元)", "val": 298244.55, "sub": []}, {"des": " 其它应收款(元)", "val": 17751116.86, "sub": []}, {"des": "存货(元)", "val": 141856397.72, "sub": []}]}, {"des": "非流动资产(元)", "val": 455987579.49, "sub": [{"des": "债券投资(元)", "val": 0.0, "sub": []}, {"des": "其他债权投资(元)", "val": 0.0, "sub": []}, {"des": "其他权益工具投资(元)", "val": 3138942.47, "sub": []}, {"des": "长期应收款(元)", "val": 0.0, "sub": []}, {"des": "长期股权投资(元)", "val": 0.0, "sub": []}, {"des": "投资性房地产(元)", "val": 0.0, "sub": []}, {"des": "固定资产(元)", "val": 92268295.7, "sub": []}, {"des": "在建工程(元)", "val": 9494315.88, "sub": []}, {"des": "使用权资产(元)", "val": 9434886.36, "sub": []}, {"des": "无形资产(元)", "val": 89181429, "sub": []}, {"des": "开发支出(元)", "val": 0.0, "sub": []}, {"des": "商誉(元)", "val": 0.0, "sub": []}, {"des": "长期待摊费用(元)", "val": 0.0, "sub": []}, {"des": "递延所得税资产(元)", "val": 13633464.91, "sub": []}, {"des": "可供出售金融资产(元)", "val": 0.0, "sub": []}, {"des": "持有至到期投资(元)", "val": 0.0, "sub": []}]}]}]}]}]}}}}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        limit = limit if limit else 3
        params = {
            "reportName": "RPT_F10_FINANCE_DUPONT",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
            "pageNumber": 1,
            "pageSize": limit,
            "sortTypes": '-1',
            "sortColumns": 'REPORT_DATE',
        }
        data, pid = self._get(url, params, 'EM_FN_DP', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{limit}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = EmDataFormatter().formate_fn_dupont(res)
        ret = Attr.group_item_by_key(ret, 'date')
        ret = {k: ret[k][0] for k in sorted(ret.keys())}
        return self._ret(ret, pid, start_time)

    def get_fn_notice_file(self, stock_code: str, sd: str, pn=1, ps=50) -> Dict:
        """
        获取股票财务公告文件

        :param str stock_code: 股票代码，如： 002107
         :param str sd: 更新日期 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int pn: 页码
        :param int ps: 条数
        :return: 股票财务公告文件
        {"total":1141,"data":[{"date":"2025-08-28","art_code":"AN202508281736010965","title":"锐奇股份:关于获得政府补助的公告","type":"获得补贴（资助）","post_time":"2025-08-28 16:23:12:249","url":"https://pdf.dfcfw.com/pdf/H2_AN202508281736010965_1.pdf"}]}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._NOTICE_URL + "/api/security/ann"
        params = {
            # "cb": "",  # jQuery1123006753685043459545_1758496803948
            "sr": -1,
            "page_index": pn,
            "page_size": ps,
            "ann_type": 'A',
            "client_source": 'web',
            "stock_list": f'{stock_code}',
            "f_node": 0,
            "s_node": 0,
        }
        data, pid = self._get(url, params, 'EM_FN_NF', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{pn},{ps}"})
        res = Attr.get_by_point(data, 'data.list', [])
        total = Attr.get_by_point(data, 'data.total_hits', 0)
        ret = [{
            'date': d['notice_date'][:10],
            'art_code': Attr.get(d, 'art_code', ''),  # 文件代码
            'title': Attr.get(d, 'title', ''),  # 文件标题
            'type': Attr.get(Attr.get_by_point(d, 'columns.0', {}), 'column_name', ''),  # 文件分类
            'post_time': d['eiTime'][:19],  # 发布时间: str - Y-m-d H:i:s  # display_time 有时会没有
            'url': f'https://pdf.dfcfw.com/pdf/H2_{Attr.get(d, 'art_code', '')}_1.pdf',  # 文件链接
        } for d in res]
        ret = {"total": total, "data": ret}  # 由于接口最多只返回 100 条，所以外面调用需要根据总数循环进行请求
        return self._ret(ret, pid, start_time)

    def get_fn_notice_txt(self, stock_code: str, art_code: str, pn: int=1) -> Dict:
        """
        获取股票财务公告文本

        :param str stock_code: 股票代码，如： 002107
        :param str art_code: 公告唯一代码，如： AN201606170015262533
        :param int pn: 页码
        :return: 股票财务公告文本
        {"page_size": 1, "title": "xxx公告标题", "content": "xxx\r\nxxx公告内容"}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._NOTICE_C_URL + "/api/content/ann"
        params = {
            # "cb": "",  # jQuery1123006753685043459545_1758496803950
            "art_code": art_code,
            "client_source": 'web',
            "page_index": pn,
        }
        data, pid = self._get(url, params, 'EM_FN_NT', {'he': f'{prefix}{stock_code}', 'hv': f"{art_code}:{pn}"})
        # {"data":{"art_code":"AN201606170015262533","attach_list":[{"attach_size":87,"attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","seq":1}],"attach_list_ch":[{"attach_size":87,"attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","seq":1}],"attach_list_en":[],"attach_size":"87","attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","attach_url_web":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","eitime":"2016-06-17 16:51:56","extend":{},"is_ai_summary":0,"is_rich":0,"is_rich2":0,"language":"0","notice_content":"证券代码：002030 证券简称：达安基因 公告编号：2016-045\r\n 中山大学达安基因股份有限公司\r\n 关于已授予股票期权注销完成的公告\r\n 本公司及董事会全体成员保证信息披露内容的真实、准确和完整，没有虚假记载、误导性陈述或重大遗漏。\r\n 中山大学达安基因股份有限公司（以下简称“公司”）第五届董事会第六次会议和第五届监事会第六次会议审议通过了《关于终止实施股票期权激励计划的预案》，并经2015年度股东大会审议通过，会议同意公司终止股票期权激励计划并注销已授予的股票期权。具体内容详见公司于2016年3月31日在《证券时报》、巨潮资讯网上刊登的《中山大学达安基因股份有限公司关于终止实施股票期权激励计划的公告》（公告编号：2016-011）。\r\n 经中国证券登记结算有限责任公司深圳分公司审核确认，公司已完成了对首期股票期权激励计划已授予的全部股票期权注销事宜，涉及激励对象67人，股票期权数量508.464万份。\r\n 特此公告。\r\n 中山大学达安基因股份有限公司\r\n 董事会\r\n 2016年6月17日\r\n","notice_date":"2016-06-18 00:00:00","notice_title":"达安基因:关于已授予股票期权注销完成的公告","page_size":1,"page_size_ch":0,"page_size_cht":0,"page_size_en":0,"security":[{"market_uni":"0","short_name":"达安基因","short_name_ch":"达安基因","short_name_cht":"達安基因","short_name_en":"DAJY","stock":"002030"}],"short_name":"达安基因"},"success":1}
        res = Attr.get_by_point(data, 'data', {})
        ret = {
            # "art_code": art_code,
            # "attach_url": res.get('attach_url', ''),
            # "post_time": res.get('eitime', ''),
            "page_size": int(res.get('page_size', 1)),  # # page_size > 1 说明有多页数据 - 外面处理
            "title": res.get('notice_title', ''),
            "content": res.get('notice_content', ''),
        }
        return self._ret(ret, pid, start_time)

    def get_fn_notice_txt_quick(self, stock_code: str, art_code: str, pn: int=1) -> Dict:
        """
        获取股票财务公告文本 - [快速模式]
          - 只请求不入库
          - 使用代理池短时间内完成大量请求

        :param str stock_code: 股票代码，如： 002107
        :param str art_code: 公告唯一代码，如： AN201606170015262533
        :param int pn: 页码
        :return: 股票财务公告文本
        """
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._NOTICE_C_URL + "/api/content/ann"
        params = {
            "art_code": art_code,
            "client_source": 'web',
            "page_index": pn,
        }
        # data, pid = self._get(url, params, 'EM_FN_NT', {'he': f'{prefix}{stock_code}', 'hv': f"{art_code}:{pn}"})
        proxy, pf = Http.get_proxy()  # 轮询隧道
        if not pf:
            raise Exception(f"Get http proxy failed: {proxy}")
        # 使用本地代理请求
        data = Http.send_request('GET', url, params, self.headers, proxy)
        # {"data":{"art_code":"AN201606170015262533","attach_list":[{"attach_size":87,"attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","seq":1}],"attach_list_ch":[{"attach_size":87,"attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","seq":1}],"attach_list_en":[],"attach_size":"87","attach_type":"0","attach_url":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","attach_url_web":"https://pdf.dfcfw.com/pdf/H2_AN201606170015262533_1.pdf?1647088592000.pdf","eitime":"2016-06-17 16:51:56","extend":{},"is_ai_summary":0,"is_rich":0,"is_rich2":0,"language":"0","notice_content":"证券代码：002030 证券简称：达安基因 公告编号：2016-045\r\n 中山大学达安基因股份有限公司\r\n 关于已授予股票期权注销完成的公告\r\n 本公司及董事会全体成员保证信息披露内容的真实、准确和完整，没有虚假记载、误导性陈述或重大遗漏。\r\n 中山大学达安基因股份有限公司（以下简称“公司”）第五届董事会第六次会议和第五届监事会第六次会议审议通过了《关于终止实施股票期权激励计划的预案》，并经2015年度股东大会审议通过，会议同意公司终止股票期权激励计划并注销已授予的股票期权。具体内容详见公司于2016年3月31日在《证券时报》、巨潮资讯网上刊登的《中山大学达安基因股份有限公司关于终止实施股票期权激励计划的公告》（公告编号：2016-011）。\r\n 经中国证券登记结算有限责任公司深圳分公司审核确认，公司已完成了对首期股票期权激励计划已授予的全部股票期权注销事宜，涉及激励对象67人，股票期权数量508.464万份。\r\n 特此公告。\r\n 中山大学达安基因股份有限公司\r\n 董事会\r\n 2016年6月17日\r\n","notice_date":"2016-06-18 00:00:00","notice_title":"达安基因:关于已授予股票期权注销完成的公告","page_size":1,"page_size_ch":0,"page_size_cht":0,"page_size_en":0,"security":[{"market_uni":"0","short_name":"达安基因","short_name_ch":"达安基因","short_name_cht":"達安基因","short_name_en":"DAJY","stock":"002030"}],"short_name":"达安基因"},"success":1}
        # 将请求结果写入到本地文件 - 方便后续处理
        file_path = Dir.abs_dir(f'storage/tmp/gpl/{prefix}{stock_code}/{art_code}-{pn}.json')
        File.save_file(data, file_path)
        return data
