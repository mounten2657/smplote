import json
import time
import random
import requests
from typing import Dict, List
from tool.core import Logger, Attr, Str, Error, Time
from model.gpl.gpl_api_log_model import GplApiLogModel

logger = Logger()


class EmDataSource:
    """
    东方财富数据源

    api_doc: https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_F10_BASIC_ORGINFO&columns=ALL&filter=(stock_code="002336.SZ")
    """

    _DATA_URL = "https://datacenter.eastmoney.com"
    _PUB_URL = "https://push2his.eastmoney.com"

    def __init__(self, timeout=30, retry_times=1):
        """
        初始化数据来源

        :param: timeout: 请求超时时间(秒)
        :param: retry_times: 请求重试次数
        """
        self.timeout = timeout
        self.retry_times = retry_times
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.eastmoney.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.session.headers.update(self.headers)
        self.ldb = GplApiLogModel()

    def get_basic_info(self, stock_code: str) -> Dict:
        """
        获取股票基本信息

        :param: stock_code: 股票代码，如: 002336
        :return: 股票基本信息字典
        {"version":"2ee4572e98feb08dc54574d9f99c9236","result":{"pages":1,"data":[{"SECUCODE":"000584.SZ","SECURITY_CODE":"000584","SECURITY_NAME_ABBR":"工智退","ORG_CODE":"10005525","ORG_NAME":"江苏哈工智能机器人股份有限公司","ORG_NAME_EN":"Jiangsu Hagong Intelligent Robot Co.,Ltd","FORMERNAME":"蜀都A→舒卡股份→G舒卡→舒卡股份→友利控股→哈工智能→ST工智→*ST工智","STR_CODEA":"000584","STR_NAMEA":"工智退","STR_CODEB":null,"STR_NAMEB":null,"STR_CODEH":null,"STR_NAMEH":null,"SECURITY_TYPE":"深交所风险警示板A股","EM2016":"机械设备-机器人-工业机器人","TRADE_MARKET":"深圳证券交易所","INDUSTRYCSRC1":"制造业-通用设备制造业","PRESIDENT":"沈进长","LEGAL_PERSON":"沈进长","SECRETARY":"沈进长(代)","CHAIRMAN":"沈进长","SECPRESENT":"张玮","INDEDIRECTORS":"王亮,杜奕良,杨敏丽","ORG_TEL":"010-60181838","ORG_EMAIL":"000584@hgzn.com","ORG_FAX":"021-51782929","ORG_WEB":"www.hgzn.com","ADDRESS":"北京西城区裕民东路5号瑞得大厦12楼","REG_ADDRESS":"江苏省江阴市临港街道双良路15号","PROVINCE":"江苏","ADDRESS_POSTCODE":"100029","REG_CAPITAL":76093.7577,"REG_NUM":"913202002019651838","EMP_NUM":1018,"TATOLNUMBER":11,"LAW_FIRM":"北京国枫(深圳)律师事务所","ACCOUNTFIRM_NAME":"尤尼泰振青会计师事务所(特殊普通合伙)","ORG_PROFILE":"    江苏哈工智能机器人股份有限公司(简称:哈工智能),是一家聚焦于高端智能装备制造和人工智能机器人的高科技上市公司(股票代码:000584.SZ)。公司业务涵盖高端智能装备制造、机器人本体、工业机器人一站式服务平台等三大板块。未来,哈工智能将从AI工业辅助设计、智能制造、AI智能检验/检测三大领域帮助中国制造业企业实现工业智能化,助推《中国制造2025》战略的实施及工业4.0的实现。","BUSINESS_SCOPE":"机器人系统、智能生产线及人工智能的研发、技术咨询、技术服务;工业机器人、工业自动控制系统装置研发、技术咨询、技术服务、技术转让、制造、销售与维修;信息系统集成服务;软件的开发、技术咨询、技术服务、技术转让、销售及维护;利用自有资金对宾馆、旅游、餐饮、娱乐行业进行投资;自有房屋租赁;国内贸易(不含国家限制及禁止类项目);自营和代理各类商品及技术的进出口业务(国家限定企业经营或禁止进出口的商品除外)。(依法须经批准的项目,经相关部门批准后方可开展经营活动)","TRADE_MARKETT":"深交所风险警示板","TRADE_MARKET_CODE":"069001002005","SECURITY_TYPEE":"A股","SECURITY_TYPE_CODE":"058001001","EXPAND_NAME_ABBRN":null,"EXPAND_NAME_PINYIN":null,"EXPAND_NAME_ABBR":null,"LISTING_DATE":"1995-11-28 00:00:00","FOUND_DATE":"1991-10-10 00:00:00","MAIN_BUSINESS":"智能制造业务","HOST_BROKER":null,"TRANSFER_WAY":null,"ACTUAL_HOLDER":"艾迪,乔徽","MARKETING_START_DATE":null,"MARKET_MAKER":null,"TRADE_MARKET_TYPE":null,"CURRENCY":"人民币"}],"count":1},"success":true,"message":"ok","code":0}
        """
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_F10_BASIC_ORGINFO",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
        }
        start_time = Time.now(0)
        data, pid = self._get(url, params, 'EM_BASIC', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data.0', {})
        return self._ret(res, pid, start_time)

    def get_issue_info(self, stock_code: str) -> Dict:
        """
        获取股票发行信息

        :param: stock_code: 股票代码，如: 002336
        :return: 股票发行信息字典
        {"version":"4e6065b3a302cef50799118f556eef46","result":{"pages":1,"data":[{"SECUCODE":"000584.SZ","SECURITY_CODE":"000584","FOUND_DATE":"1991-10-10 00:00:00","LISTING_DATE":"1995-11-28 00:00:00","AFTER_ISSUE_PE":null,"ONLINE_ISSUE_DATE":"1986-07-01 00:00:00","ISSUE_WAY":"其他发行方式","PAR_VALUE":1,"TOTAL_ISSUE_NUM":35000000,"ISSUE_PRICE":3.5,"DEC_SUMISSUEFEE":null,"TOTAL_FUNDS":122500000,"NET_RAISE_FUNDS":null,"OPEN_PRICE":6.8,"CLOSE_PRICE":7.31,"TURNOVERRATE":36.9577,"HIGH_PRICE":7.38,"OFFLINE_VAP_RATIO":null,"ONLINE_ISSUE_LWR":null,"SECURITY_TYPE":"A股","OVERALLOTMENT":null,"TYPE":"2","TRADE_MARKET_CODE":"069001002005","STR_ZHUCHENGXIAO":"成都蜀都大厦股份有限公司(自主发行)","STR_BAOJIAN":"大鹏证券有限责任公司,上海申银证券有限公司,北京标准股份制咨询公司"}],"count":1},"success":true,"message":"ok","code":0}
        """
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._DATA_URL + "/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_PCF10_ORG_ISSUEINFO",
            "columns": "ALL",
            "filter": f'(SECUCODE="{stock_code}.{prefix}")',
        }
        start_time = Time.now(0)
        data, pid = self._get(url, params, 'EM_ISSUE', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data.0', {})
        return self._ret(res, pid, start_time)

    def get_concept_info(self, stock_code: str) -> Dict:
        """
        获取股票概念板块信息

        :param: stock_code: 股票代码，如: 002336
        :return: list
        [{"SECUCODE":"603316.SH","SECURITY_CODE":"603316","SECURITY_NAME_ABBR":"诚邦股份","BOARD_CODE":"425","BOARD_NAME":"工程建设","SELECTED_BOARD_REASON":"None","IS_PRECISE":"0","BOARD_RANK":1,"BOARD_YIELD":"None","NEW_BOARD_CODE":"BK0425","DERIVE_BOARD_CODE":"BI0425","BOARD_TYPE":"行业","BOARD_LEVEL":"None"}]
        """
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
        start_time = Time.now(0)
        data, pid = self._get(url, params, 'EM_CONCEPT', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data', {})
        return self._ret(res, pid, start_time)

    def get_concept_text(self, stock_code: str) -> Dict:
        """
        获取股票概念板块核心题材

        :param: stock_code: 股票代码，如: 002336
        :return: list
        [{"SECUCODE":"603316.SH","SECURITY_CODE":"603316","SECURITY_NAME_ABBR":"诚邦股份","KEYWORD":"经营范围","MAINPOINT":2,"MAINPOINT_CONTENT":"环境治理工程、土壤修复工程、水污染治理工程、大气污染治理工程、地质灾害治理工程、固体废物治理工程的设计、施工、运营管理,园林绿化工程、市政工程、园林古建筑工程、房屋建筑工程、土石方工程、水利水电工程、公路工程、建筑智能化工程、照明工程的施工、养护及运营管理,城乡规划设计,旅游信息咨询,旅游项目开发,景区管理服务,旅游服务(不含旅行社),文化创意策划,花木种植、销售,园林机械、建筑材料、初级食用农产品的销售;实业投资。(以公司登记机关核定的经营范围为准)","KEY_CLASSIF":"经营范围","KEY_CLASSIF_CODE":"002","IS_POINT":"0","MAINPOINT_NUM":"要点二","MAINPOINT_RANK":2,"IS_HISTORY":"0","SECURITY_CODE4":"603316"}]
        """
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
        start_time = Time.now(0)
        data, pid = self._get(url, params, 'EM_CONCEPT_TEXT', {'he': f'{prefix}{stock_code}', 'hv': Time.date('%Y-%m-%d')})
        res = Attr.get_by_point(data, 'result.data', {})
        return self._ret(res, pid, start_time)

    def get_daily_quote(self, stock_code: str, sd: str = "20000101", ed: str = "20990101", adjust: str = "", period: str = "daily") -> List[Dict]:
        """
        获取股票日线行情

        :param str stock_code: 股票代码，格式如"002336"
        :param str sd: 开始日期 - Ymd （如： 20250301）
        :param str ed: 结束日期 - Ymd（如： 20250302）
        :param str adjust: key of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
        :param str period: key of {"qfq": "1", "hfq": "2", "": "0"}
        :return: 日线行情数据列表，每个元素为一个交易日数据字典
        [{'date': '2025-06-27', 'open': 7.13, 'close': 7.19, 'high': 7.19, 'low': 7.06, 'volume': 41573, 'amount': 29676241.0, 'amplitude': 1.83, 'pct_change': 1.13, 'price_change': 0.08, 'turnover_rate': 1.97}]
        """
        stock_code, prefix, prefix_int = self._format_stock_code(stock_code)
        url = self._PUB_URL + "/api/qt/stock/kline/get"
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
        start_time = Time.now(0)
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
            try:
                # 添加随机延迟，避免频繁请求
                time.sleep(random.uniform(0.1, 0.9))
                # 如果已经有了日志数据就不用请求接口了
                pid = self.ldb.add_gpl_api_log(url, params, biz_code, ext)
                if isinstance(pid, dict):
                    return pid['response_result'], 0
                response = self.session.get(url, params=params, timeout=self.timeout)
                # 检查请求是否成功
                response.raise_for_status()
                # 解析JSON数据
                # print(response.text)
                data = response.json()
                self.ldb.update_gpl_api_log(pid, {'response_result': data})
                return data, pid
            except requests.RequestException as e:
                err = Error.handle_exception_info(e)
                logger.warning(f"请求失败 ({i + 1}/{self.retry_times}): {url}, 错误 - {err}", 'EM_API_ERR')
                if i == self.retry_times - 1:
                    return None, 0
            except json.JSONDecodeError:
                logger.warning(f"JSON解析失败 - {url} - {params}", 'EM_API_ERR')
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
