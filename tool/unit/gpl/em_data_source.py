import requests
from typing import Dict, List
from tool.core import Logger, Attr, Str, Error, Time, Http
from model.gpl.gpl_api_log_model import GplApiLogModel
from service.vps.open_nat_service import OpenNatService

logger = Logger()


class EmDataSource:
    """
    东方财富数据源

    api_doc: https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_BASIC_ORGINFO&columns=ALL&filter=(stock_code="002336.SZ")
    """

    _DATA_URL = "https://datacenter.eastmoney.com"
    _PUSH_URL = "https://push2his.eastmoney.com"
    _EWEB_URL = "https://emweb.securities.eastmoney.com"

    def __init__(self, timeout=30, retry_times=1):
        """
        初始化数据来源

        :param: timeout: 请求超时时间(秒)
        :param: retry_times: 请求重试次数
        """
        self.timeout = timeout
        self.retry_times = retry_times
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.35 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.35',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.eastmoney.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.ldb = GplApiLogModel()

    def _get(self, url: str, params: Dict = None, biz_code='', ext=None):
        """
        发送GET请求并处理响应

        :param: url: 请求URL
        :param: params: 请求参数
        :param: biz_code: 业务代码
        :param: ext: 额外参数
        :return: 解析后的JSON数据，失败返回None
        """
        for i in range(self.retry_times):
            info = {}
            pid = 0
            try:
                rand = Str.randint(1, 10000) % 2
                params['nat_int'] = rand
                # 如果已经有了日志数据就不用请求接口了
                if any(c in biz_code for c in ['EM_DAILY', 'EM_GD', 'EM_FN', 'EM_DV', 'EM_ZY']):
                    pid = self.ldb.add_gpl_api_log(url, params, biz_code, ext)
                    if isinstance(pid, dict):
                        if pid['response_result'] and isinstance(pid['response_result'], dict):
                            return pid['response_result'], 0
                        else:
                            info = pid
                            pid = pid['id']
                # 由于同一台机器短时间内大量请求会被封，所以这里用不同机器进行分流
                rand = (pid % 2) if pid else rand
                # rand = 1  # 机器坏了，先指定固定的
                params['nat_int'] = rand
                self.headers['Referer'] = Http.get_request_base_url(url)
                if 1 == rand:
                    # 使用 nat 请求
                    data = OpenNatService.send_http_request('GET', url, params, self.headers, self.timeout)
                else:
                    # 使用本地请求
                    data = Http.send_request('GET', url, params, self.headers)
                if pid and not info.get('response_result'):
                    self.ldb.update_gpl_api_log(pid, {'response_result': data if data else {}, 'request_params': params})

                return data, pid
            except Exception as e:
                err = Error.handle_exception_info(e)
                logger.warning(f"请求失败 ({i + 1}/{self.retry_times}): {url} - {params} - 错误 - {err}", 'EM_API_ERR')
                if i == self.retry_times - 1:
                    return None, 0

    def _ret(self, res, pid, start_time):
        """格式化返回"""
        run_time = round(Time.now(0) - start_time, 3) * 1000
        res and self.ldb.update_gpl_api_log(pid, {'process_params': res, 'is_succeed': 1, 'response_time': run_time})
        return res

    def _format_stock_code(self, stock_code):
        """格式化股票代码"""
        stock_code = Str.remove_stock_prefix(stock_code)
        prefix = Str.get_stock_prefix(stock_code)
        prefix_int = 1 if 'SH' == prefix else 0
        return stock_code, prefix, prefix_int

    def get_basic_info(self, stock_code: str) -> Dict:
        """
        获取股票基本信息

        :param str stock_code: 股票代码，如： 002107
        :return: 股票基本信息字典
        {"version":"2ee4572e98feb08dc54574d9f99c9236","result":{"pages":1,"data":[{"SECUCODE":"000584.SZ","SECURITY_CODE":"000584","SECURITY_NAME_ABBR":"工智退","ORG_CODE":"10005525","ORG_NAME":"江苏哈工智能机器人股份有限公司","ORG_NAME_EN":"Jiangsu Hagong Intelligent Robot Co.,Ltd","FORMERNAME":"蜀都A→舒卡股份→G舒卡→舒卡股份→友利控股→哈工智能→ST工智→*ST工智","STR_CODEA":"000584","STR_NAMEA":"工智退","STR_CODEB":null,"STR_NAMEB":null,"STR_CODEH":null,"STR_NAMEH":null,"SECURITY_TYPE":"深交所风险警示板A股","EM2016":"机械设备-机器人-工业机器人","TRADE_MARKET":"深圳证券交易所","INDUSTRYCSRC1":"制造业-通用设备制造业","PRESIDENT":"沈进长","LEGAL_PERSON":"沈进长","SECRETARY":"沈进长(代)","CHAIRMAN":"沈进长","SECPRESENT":"张玮","INDEDIRECTORS":"王亮,杜奕良,杨敏丽","ORG_TEL":"010-60181838","ORG_EMAIL":"000584@hgzn.com","ORG_FAX":"021-51782929","ORG_WEB":"www.hgzn.com","ADDRESS":"北京西城区裕民东路5号瑞得大厦12楼","REG_ADDRESS":"江苏省江阴市临港街道双良路15号","PROVINCE":"江苏","ADDRESS_POSTCODE":"100029","REG_CAPITAL":76093.7577,"REG_NUM":"913202002019651838","EMP_NUM":1018,"TATOLNUMBER":11,"LAW_FIRM":"北京国枫(深圳)律师事务所","ACCOUNTFIRM_NAME":"尤尼泰振青会计师事务所(特殊普通合伙)","ORG_PROFILE":"    江苏哈工智能机器人股份有限公司(简称:哈工智能),是一家聚焦于高端智能装备制造和人工智能机器人的高科技上市公司(股票代码:000584.SZ)。公司业务涵盖高端智能装备制造、机器人本体、工业机器人一站式服务平台等三大板块。未来,哈工智能将从AI工业辅助设计、智能制造、AI智能检验/检测三大领域帮助中国制造业企业实现工业智能化,助推《中国制造2025》战略的实施及工业4.0的实现。","BUSINESS_SCOPE":"机器人系统、智能生产线及人工智能的研发、技术咨询、技术服务;工业机器人、工业自动控制系统装置研发、技术咨询、技术服务、技术转让、制造、销售与维修;信息系统集成服务;软件的开发、技术咨询、技术服务、技术转让、销售及维护;利用自有资金对宾馆、旅游、餐饮、娱乐行业进行投资;自有房屋租赁;国内贸易(不含国家限制及禁止类项目);自营和代理各类商品及技术的进出口业务(国家限定企业经营或禁止进出口的商品除外)。(依法须经批准的项目,经相关部门批准后方可开展经营活动)","TRADE_MARKETT":"深交所风险警示板","TRADE_MARKET_CODE":"069001002005","SECURITY_TYPEE":"A股","SECURITY_TYPE_CODE":"058001001","EXPAND_NAME_ABBRN":null,"EXPAND_NAME_PINYIN":null,"EXPAND_NAME_ABBR":null,"LISTING_DATE":"1995-11-28 00:00:00","FOUND_DATE":"1991-10-10 00:00:00","MAIN_BUSINESS":"智能制造业务","HOST_BROKER":null,"TRANSFER_WAY":null,"ACTUAL_HOLDER":"艾迪,乔徽","MARKETING_START_DATE":null,"MARKET_MAKER":null,"TRADE_MARKET_TYPE":null,"CURRENCY":"人民币"}],"count":1},"success":true,"message":"ok","code":0}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_BASIC_ORGINFO",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
        }
        data, pid = self._get(url, params, 'EM_INF_BASIC', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data.0', {})
        return self._ret(res, pid, start_time)

    def get_issue_info(self, stock_code: str) -> Dict:
        """
        获取股票发行信息

        :param str stock_code: 股票代码，如： 002107
        :return: 股票发行信息字典
        {"version":"4e6065b3a302cef50799118f556eef46","result":{"pages":1,"data":[{"SECUCODE":"000584.SZ","SECURITY_CODE":"000584","FOUND_DATE":"1991-10-10 00:00:00","LISTING_DATE":"1995-11-28 00:00:00","AFTER_ISSUE_PE":null,"ONLINE_ISSUE_DATE":"1986-07-01 00:00:00","ISSUE_WAY":"其他发行方式","PAR_VALUE":1,"TOTAL_ISSUE_NUM":35000000,"ISSUE_PRICE":3.5,"DEC_SUMISSUEFEE":null,"TOTAL_FUNDS":122500000,"NET_RAISE_FUNDS":null,"OPEN_PRICE":6.8,"CLOSE_PRICE":7.31,"TURNOVERRATE":36.9577,"HIGH_PRICE":7.38,"OFFLINE_VAP_RATIO":null,"ONLINE_ISSUE_LWR":null,"SECURITY_TYPE":"A股","OVERALLOTMENT":null,"TYPE":"2","TRADE_MARKET_CODE":"069001002005","STR_ZHUCHENGXIAO":"成都蜀都大厦股份有限公司(自主发行)","STR_BAOJIAN":"大鹏证券有限责任公司,上海申银证券有限公司,北京标准股份制咨询公司"}],"count":1},"success":true,"message":"ok","code":0}
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_PCF10_ORG_ISSUEINFO",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
        }
        data, pid = self._get(url, params, 'EM_INF_ISSUE', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data.0', {})
        return self._ret(res, pid, start_time)

    def get_concept_info(self, stock_code: str) -> Dict:
        """
        获取股票概念板块信息

        :param str stock_code: 股票代码，如： 002107
        :return: list
        [{"SECUCODE":"603316.SH","SECURITY_CODE":"603316","SECURITY_NAME_ABBR":"诚邦股份","BOARD_CODE":"425","BOARD_NAME":"工程建设","SELECTED_BOARD_REASON":"None","IS_PRECISE":"0","BOARD_RANK":1,"BOARD_YIELD":"None","NEW_BOARD_CODE":"BK0425","DERIVE_BOARD_CODE":"BI0425","BOARD_TYPE":"行业","BOARD_LEVEL":"None"}]
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/get"
        params = {
            "type": "RPT_F10_CORETHEME_BOARDTYPE",
            "sty": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
            "st": "BOARD_RANK",
            "source": "HSF10",
            "client": "PC",
            "sr": "1",
            "p": "1",
            "v": "013032671915799998",
        }
        data, pid = self._get(url, params, 'EM_CONCEPT', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data', {})
        return self._ret(res, pid, start_time)

    def get_concept_text(self, stock_code: str) -> Dict:
        """
        获取股票概念板块核心题材

        :param str stock_code: 股票代码，如: 002336
        :return: list
        [{"SECUCODE":"603316.SH","SECURITY_CODE":"603316","SECURITY_NAME_ABBR":"诚邦股份","KEYWORD":"经营范围","MAINPOINT":2,"MAINPOINT_CONTENT":"环境治理工程、土壤修复工程、水污染治理工程、大气污染治理工程、地质灾害治理工程、固体废物治理工程的设计、施工、运营管理,园林绿化工程、市政工程、园林古建筑工程、房屋建筑工程、土石方工程、水利水电工程、公路工程、建筑智能化工程、照明工程的施工、养护及运营管理,城乡规划设计,旅游信息咨询,旅游项目开发,景区管理服务,旅游服务(不含旅行社),文化创意策划,花木种植、销售,园林机械、建筑材料、初级食用农产品的销售;实业投资。(以公司登记机关核定的经营范围为准)","KEY_CLASSIF":"经营范围","KEY_CLASSIF_CODE":"002","IS_POINT":"0","MAINPOINT_NUM":"要点二","MAINPOINT_RANK":2,"IS_HISTORY":"0","SECURITY_CODE4":"603316"}]
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/get"
        params = {
            "type": "RPT_F10_CORETHEME_CONTENT",
            "sty": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")(KEY_CLASSIF_CODE<>"001")',
            "st": "KEY_CLASSIF_CODE,MAINPOINT",
            "source": "HSF10",
            "client": "PC",
            "sr": "1,1",
            "p": "1",
            "v": "013032671915799998",
        }
        data, pid = self._get(url, params, 'EM_CONCEPT_TEXT', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data', {})
        return self._ret(res, pid, start_time)

    def get_daily_quote(self, stock_code: str, sd: str = "20000101", ed: str = "20990101", adjust: str = "", period: str = "daily") -> List[Dict]:
        """
        获取股票日线行情

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 开始日期 - Ymd 或 Y-m-d（如： 2025-03-01）
        :param str ed: 结束日期 - Ymd 或 Y-m-d（如： 2025-03-02）
        :param str adjust: key of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
        :param str period: key of {"qfq": "1", "hfq": "2", "": "0"}
        :return: 日线行情数据列表，每个元素为一个交易日数据字典
        [{'date': '2025-06-27', 'open': 7.13, 'close': 7.19, 'high': 7.19, 'low': 7.06, 'volume': 41573, 'amount': 29676241.0, 'amplitude': 1.83, 'pct_change': 1.13, 'price_change': 0.08, 'turnover_rate': 1.97}]
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._PUSH_URL + "/api/qt/stock/kline/get"
        period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
        adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
        params = {
            "secid": f"{prefix_int}.{stock_code}",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fields1": "f1,f2,f3,f4,f5,f6",  # '股票代码', '市场代码(0: 深,1: 沪)', '股票名称'
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",  # '日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率'
            "klt": period_dict[period],  # K线类型：101=日线，102=周线，103=月线，15=15分钟，5=5分钟
            "fqt": adjust_dict[adjust],  # 复权类型：0=不复权，1=前复权，2=后复权
            "beg": (sd if sd else "19700101").replace('-', ''),  # 兼容 Y-m-d
            "end": (ed if ed else "99991231").replace('-', ''),  # 兼容 Y-m-d
            "isSecurity": "0",
            "lmt": "10000",
        }
        data, pid = self._get(url, params, f'EM_DAILY_{adjust_dict[adjust]}', {'he': f'{prefix}{stock_code}', 'hv': f'{sd}~{ed}'})
        kline_list = Attr.get_by_point(data, 'data.klines', [])
        if not kline_list:
            return []
        # 解析K线数据
        daily_data = []
        for kline in kline_list:
            parts = kline.split(',')
            if not float(parts[1]) and not float(parts[2]):
                continue
            daily_data.append({
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": int(parts[5]),
                "amount": float(parts[6]) if len(parts) > 6 else 0,
                "amplitude": float(parts[7]) if len(parts) > 7 else 0,
                "pct_change": float(parts[8]) if len(parts) > 8 else 0,
                "price_change": float(parts[9]) if len(parts) > 9 else 0,
                "turnover_rate": float(parts[10]) if len(parts) > 10 else 0,
            })
        return self._ret(daily_data, pid, start_time)

    def get_gd_top10(self, stock_code: str, sd: str, limit: int = 1, is_special: int = 0) -> List:
        """
        获取股票十大股东列表

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 季度尾日 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int limit: 返回条数
        :param int is_special: 是否为特殊股票 - 针对那些无法正常获取股东信息的股票，约10只
        :return: 股票十大股东列表
        [{"rank": 1, "gd_name": "潘华荣", "gf_type": "流通A股,限售流通A股", "gf_num": 129245978, "rate": 19.0, "c_type": "不变", "c_val": 0.0}, {"rank": 2, "gd_name": "孙永杰", "gf_type": "流通A股,限售流通A股", "gf_num": 79920000, "rate": 11.75, "c_type": "不变", "c_val": 0.0}, {"rank": 3, "gd_name": "徐英盖", "gf_type": "流通A股", "gf_num": 14227488, "rate": 2.09, "c_type": "不变", "c_val": 0.0}, {"rank": 4, "gd_name": "香港中央结算有限公司", "gf_type": "流通A股", "gf_num": 9878502, "rate": 1.45, "c_type": "3459873", "c_val": 53.903614}, {"rank": 5, "gd_name": "金福芽", "gf_type": "流通A股", "gf_num": 5434782, "rate": 0.8, "c_type": "不变", "c_val": 0.0}, {"rank": 6, "gd_name": "陈年村", "gf_type": "流通A股", "gf_num": 3263580, "rate": 0.48, "c_type": "不变", "c_val": 0.0}, {"rank": 7, "gd_name": "郑素婵", "gf_type": "流通A股", "gf_num": 2330000, "rate": 0.34, "c_type": "-2595000", "c_val": -52.69035533}, {"rank": 8, "gd_name": "张苏叶", "gf_type": "流通A股", "gf_num": 2223600, "rate": 0.33, "c_type": "新进", "c_val": 0.0}, {"rank": 9, "gd_name": "黄光辉", "gf_type": "流通A股", "gf_num": 2000000, "rate": 0.29, "c_type": "新进", "c_val": 0.0}, {"rank": 10, "gd_name": "叶选朋", "gf_type": "流通A股", "gf_num": 1776580, "rate": 0.26, "c_type": "新进", "c_val": 0.0}]
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        if not is_special:
            url = self._EWEB_URL + "/PC_HSF10/ShareholderResearch/PageSDGD"
            params = {
                "code": f"{prefix}{stock_code}",
                "date": f"{sd}",
            }
            data, pid = self._get(url, params, 'EM_GD_TOP10', {'he': f'{prefix}{stock_code}', 'hv': sd})
            res = Attr.get_by_point(data, 'sdgd', [])
        else:
            url = self._DATA_URL + "/securities/api/data/v1/get"
            params = {
                "reportName": "RPT_F10_EH_HOLDERS",
                "columns": "ALL",
                "filter": f'(SECUCODE="{stock_code}.{prefix}")',  # 还有个 END_DATE , 但是日期没有规律，就不传了
                "pageNumber": 1,
                "pageSize": limit,
                "sortTypes": 1,
                "sortColumns": "HOLDER_RANK",
                "source": "HSF10",
            }
            data, pid = self._get(url, params, 'EM_GD_TOP10', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{limit}"})
            res = Attr.get_by_point(data, 'result.data', [])
        ret = [{
            'date': d['END_DATE'][:10],
            'rank': d['HOLDER_RANK'],  # 排名
            'gd_name': d['HOLDER_NAME'],  # 股东名
            'gf_type': d['SHARES_TYPE'],  # 股份类型： A股
            'gf_num': d['HOLD_NUM'],  # 持股数量
            'rate': d['HOLD_NUM_RATIO'],  # 持股比例
            'c_type': d['HOLD_NUM_CHANGE'],  # 持股增减： 不变 | 增加 | 减少
            'c_val': float(d['CHANGE_RATIO']) if d['CHANGE_RATIO'] else 0.0,  # 持股变化率
        } for d in res]
        return self._ret(ret, pid, start_time)

    def get_gd_top10_free(self, stock_code: str, sd: str) -> List:
        """
        获取股票十大流通股东列表

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 季度尾日 - Ymd 或 Y-m-d（如： 2025-03-31）
        :return: 股票十大流通股东列表
        [{"rank": 1, "gd_name": "北京中证万融投资集团有限公司", "gd_type": "投资公司", "gf_type": "A股", "gf_num": 290146363, "rate": 50.937128154523, "c_type": "不变", "c_val": 0.0}, {"rank": 2, "gd_name": "招商银行股份有限公司-博道远航混合型证券投资基金", "gd_type": "证券投资基金", "gf_type": "A股", "gf_num": 4964131, "rate": 0.87148628819, "c_type": "2071072", "c_val": 71.58761712}, {"rank": 3, "gd_name": "吕良丰", "gd_type": "个人", "gf_type": "A股", "gf_num": 3069106, "rate": 0.538802017111, "c_type": "176775", "c_val": 6.11185234}, {"rank": 4, "gd_name": "张戈", "gd_type": "个人", "gf_type": "A股", "gf_num": 2514688, "rate": 0.441470241433, "c_type": "不变", "c_val": 0.0}, {"rank": 5, "gd_name": "贺文猛", "gd_type": "个人", "gf_type": "A股", "gf_num": 2167900, "rate": 0.380589296328, "c_type": "34900", "c_val": 1.63619316}, {"rank": 6, "gd_name": "广发证券股份有限公司-博道成长智航股票型证券投资基金", "gd_type": "证券投资基金", "gf_type": "A股", "gf_num": 2105200, "rate": 0.369581893366, "c_type": "487580", "c_val": 30.14181328}, {"rank": 7, "gd_name": "吴经琴", "gd_type": "个人", "gf_type": "A股", "gf_num": 1937660, "rate": 0.340169129537, "c_type": "不变", "c_val": 0.0}, {"rank": 8, "gd_name": "张法忠", "gd_type": "个人", "gf_type": "A股", "gf_num": 1891395, "rate": 0.332047000382, "c_type": "不变", "c_val": 0.0}, {"rank": 9, "gd_name": "MORGAN STANLEY & CO. INTERNATIONAL PLC.", "gd_type": "QFII", "gf_type": "A股", "gf_num": 1847619, "rate": 0.324361831769, "c_type": "新进", "c_val": 0.0}, {"rank": 10, "gd_name": "钱文奇", "gd_type": "个人", "gf_type": "A股", "gf_num": 1412280, "rate": 0.247935168328, "c_type": "新进", "c_val": 0.0}]
        """
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._EWEB_URL + "/PC_HSF10/ShareholderResearch/PageSDLTGD"
        params = {
            "code": f"{prefix}{stock_code}",
            "date": f"{sd}",
        }
        start_time = Time.now(0)
        data, pid = self._get(url, params, 'EM_GD_TOP10_FREE', {'he': f'{prefix}{stock_code}', 'hv': sd})
        res = Attr.get_by_point(data, 'sdltgd', [])
        ret = [{
            'rank': d['HOLDER_RANK'],  # 排名
            'gd_name': d['HOLDER_NAME'],  # 股东名
            'gd_type': d['HOLDER_TYPE'],  # 股东类型： 个人 | 投资公司 | 机构
            'gf_type': d['SHARES_TYPE'],  # 股份类型： A股
            'gf_num': d['HOLD_NUM'],  # 持股数量
            'rate': d['FREE_HOLDNUM_RATIO'],  # 持股比例
            'c_type': d['HOLD_NUM_CHANGE'],  # 持股增减： 不变 | 增加 | 减少
            'c_val': float(d['CHANGE_RATIO']) if d['CHANGE_RATIO'] else 0.0,  # 持股变化率
        } for d in res]
        return self._ret(ret, pid, start_time)

    def get_gd_num(self, stock_code: str, td: str, limit: int = 1, is_all: int = 0) -> List:
        """
        获取股票股东人数信息

        :param str stock_code: 股票代码，如： 002107
        :param str td: 更新日期 - Y-m-d（如： 2025-03-31）
        :param int limit: 返回条数
        :param int is_all: 是否返回全部
        :return: 股票股东人数信息
        [{"date": "2025-06-30 ", "total_num": 34990, "total_rate": 1.4909, "avg_free": 16279, "avg_free_rate": -1.468991140326, "des": "较分散", "price": 5.72, "avg_money": 93118.2405830237, "t10_gd_rate": 54.84266824, "t10_gd_free_rate": 54.24930627}, {"date": "2025-03-31 ", "total_num": 34476, "total_rate": -1.7246, "avg_free": 16522, "avg_free_rate": 1.754843949414, "des": "较分散", "price": 4.43, "avg_money": 73192.9968528832, "t10_gd_rate": 55.36990497, "t10_gd_free_rate": 54.78357102}]
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        is_all_str = '' if is_all else f"(END_DATE='{td}')"
        params = {
            "reportName": "RPT_F10_EH_HOLDERNUM",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}"){is_all_str}',
            "pageNumber": 1,
            "pageSize": limit,
            "sortColumns": 'END_DATE',
            "source": 'HSF10',
        }
        data, pid = self._get(url, params, 'EM_GD_NUM', {'he': f'{prefix}{stock_code}', 'hv': f"{td}~{is_all}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['END_DATE'][:10],
            'total_num': Attr.get(d, 'HOLDER_TOTAL_NUM', 0),  # 总股东人数（户）
            'total_change_rate': Attr.get(d, 'TOTAL_NUM_RATIO', 0.0),  # 总股东人数较上期变化
            'avg_free': Attr.get(d, 'AVG_FREE_SHARES', 0.0),  # 人均流通股数
            'avg_free_change_rate': Attr.get(d, 'AVG_FREESHARES_RATIO', 0.0),  # 人均流通股数较上期变化
            'des': Attr.get(d, 'HOLD_FOCUS', ''),  # 筹码集中度： 较集中 | 较松散
            'price': Attr.get(d, 'PRICE', 0.0),  # 股价（元）
            'avg_money': Attr.get(d, 'AVG_HOLD_AMT', 0.0),  # 人均持股金额
            't10_gd_rate': Attr.get(d, 'HOLD_RATIO_TOTAL', 0.0),  # 十大股东持股占比
            't10_gd_free_rate': Attr.get(d, 'FREEHOLD_RATIO_TOTAL', 0.0),  # 十大流通股东持股占比
        } for d in res]
        return self._ret(ret, pid, start_time)

    def get_gd_org_total(self, stock_code: str, td: str, is_all: int = 0) -> List:
        """
        获取股票股东机构持仓总计

        :param str stock_code: 股票代码，如： 002107
        :param str td: 更新日期 - Y-m-d（如： 2025-03-31）
        :param int is_all: 是否返回全部
        :return: 股票股东机构持仓总计
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        is_all_str = '' if is_all else f"(REPORT_DATE='{td}')"
        params = {
            "reportName": "RPT_F10_MAIN_ORGHOLDDETAILS",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")(ORG_TYPE="00"){is_all_str}',
            "pageNumber": 1,
            "sortColumns": 'REPORT_DATE',
            "source": 'HSF10',
        }
        data, pid = self._get(url, params, 'EM_GD_ORG_T', {'he': f'{prefix}{stock_code}', 'hv': f"{td}~{is_all}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],
            'total_org': Attr.get(d, 'TOTAL_ORG_NUM', 0),  # 总机构数
            'total_hand': Attr.get(d, 'TOTAL_SHARES', 0),  # 总持股数
            'total_free_hand': Attr.get(d, 'TOTAL_FREE_SHARES', 0),  # 总流通持股数（计算总市值时用这个）
            'total_money': Attr.get(d, 'TOTAL_MARKET_CAP', 0.0),  # 总市值
            'total_free_rate': Attr.get(d, 'TOTAL_SHARES_RATIO', 0.0),  # 占流通股比
            'total_all_rate': Attr.get(d, 'ALL_SHARES_RATIO', 0.0),  # 占总股比
            'free_change_rate': Attr.get(d, 'CHANGE_RATIO', 0.0),  # 流通股市值变化率
            'free_change_vol': Attr.get(d, 'FREE_SHARES_CHANGE', 0.0),  # 占流通股比的变化量
        } for d in res]
        return self._ret(ret, pid, start_time)

    def get_gd_org_detail(self, stock_code: str, sd: str, is_all: int = 0) -> List:
        """
        获取股票股东机构持仓详细

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 季度尾日 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int is_all: 是否返回全部
        :return: 股票股东机构持仓详细
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        is_all_str = '' if is_all else f"(REPORT_DATE='{sd}')"
        params = {
            "reportName": "RPT_F10_MAIN_ORGHOLDDETAILS",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}"){is_all_str}',
            "pageNumber": 1,
            "sortColumns": 'ORG_TYPE',
            "source": 'HSF10',
        }
        data, pid = self._get(url, params, 'EM_GD_ORG_D', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{is_all}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],
            'total_org': Attr.get(d, 'TOTAL_ORG_NUM', 0),  # 总机构数
            'des': Attr.get(d, 'ORG_NAME_TYPE', ''),  # 机构名称
            'org_type': Attr.get(d, 'ORG_TYPE', ''),  # 机构类型： 00:合计 | 01:基金 | 02:QFII | 03:社保 | 04:券商 | 05:保险 | 06:信托 | 07:其它
            'total_hand': Attr.get(d, 'TOTAL_FREE_SHARES', 0),  # 持仓手数
            'total_money': Attr.get(d, 'TOTAL_MARKET_CAP', 0.0),  # 持仓总市值
            'total_free_hand_change': Attr.get(d, 'TOTAL_FREE_SHARES_CHANGE', 0.0),  # 持仓手数变化率
            'total_all_rate': Attr.get(d, 'TOTAL_SHARES_RATIO', 0.0),  # 占总流通股比
            'total_free_rate': Attr.get(d, 'ALL_SHARES_RATIO', 0.0),  # 占总股比
            'free_change_rate': Attr.get(d, 'CHANGE_RATIO', 0.0),  # 流通股市值变化率
            'free_change_vol': Attr.get(d, 'FREE_SHARES_CHANGE', 0.0),  # 占流通股比的变化量
        } for d in res]
        ret = Attr.group_item_by_key(reversed(ret), 'date')
        return self._ret(ret, pid, start_time)

    def get_gd_org_list(self, stock_code: str, sd: str, is_all: int = 0) -> List:
        """
        获取股票股东机构持仓列表

        :param str stock_code: 股票代码，如： 002107
        :param str sd: 季度尾日 - Ymd 或 Y-m-d（如： 2025-03-31）
        :param int is_all: 是否返回全部
        :return: 股票股东机构持仓列表
        """
        start_time = Time.now(0)
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        # 附加条件，网页展示的数据 -  '(ORG_TYPE="01")'
        is_all_str = '' if is_all else f"(REPORT_DATE='{sd}')"
        params = {
            "reportName": "RPT_MAIN_ORGHOLDDETAIL",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}"){is_all_str}',
            "quoteColumns": '',
            "pageNumber": 1,
            "sortTypes": -1,
            "sortColumns": 'TOTAL_SHARES',
            "source": 'HSF10',
        }
        data, pid = self._get(url, params, 'EM_GD_ORG_L', {'he': f'{prefix}{stock_code}', 'hv': f"{sd}~{is_all}"})
        res = Attr.get_by_point(data, 'result.data', {})
        ret = [{
            'date': d['REPORT_DATE'][:10],
            'des': Attr.get(d, 'HOLDER_NAME', ''),  # 机构名称
            'org_type': Attr.get(d, 'ORG_TYPE', ''),  # 机构类型： 00:合计 | 01:基金 | 02:QFII | 03:社保 | 04:券商 | 05:保险 | 06:信托 | 07:其它
            'stock_code': Attr.get(d, 'FUND_CODE', ''),  # 持股机构股票代码
            'derive_code': Attr.get(d, 'FUND_DERIVECODE', ''),  # 持股机构股票代码
            'sec_code': Attr.get(d, 'SECUCODE', ''),  # 持股机构股票代码
            'free_hand': Attr.get(d, 'FREE_SHARES', 0),  # 流通股持仓手数
            'free_money': Attr.get(d, 'FREE_MARKET_CAP', 0.0),  # 流通股持仓总市值
            'total_hand': Attr.get(d, 'TOTAL_SHARES', 0),  # 总持仓手数
            'total_money': Attr.get(d, 'HOLD_VALUE', 0.0),  # 总持仓总市值
            'total_all_rate': Attr.get(d, 'FREESHARES_RATIO', 0.0),  # 占总流通股比
            'total_free_rate': Attr.get(d, 'TOTALSHARES_RATIO', 0.0),  # 占总股比
            'total_jz_rate': Attr.get(d, 'NETVALUE_RATIO', 0.0),  # 占总净值比
        } for d in res]
        ret = Attr.group_item_by_key(reversed(ret), 'date')
        return self._ret(ret, pid, start_time)

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
        data, pid = self._get(url, params, 'EM_TB', {'he': f'{prefix}{stock_code}', 'hv': f"{Time.date('%Y-%m-%d')}"})
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

