import akshare as ak
from tool.core import Logger, Error

logger = Logger()


class AkshareData:
    """
    akshare数据源

    api_doc: https://akshare.akfamily.xyz/data/stock/stock.html#id1
    """

    def __init__(self, data_type='json'):
        self.data_type = data_type

    def _formatter(self, ak_api):
        """AK数据格式化"""
        try:
            res = ak_api()
            if 'json' == self.data_type:
                res = res.to_dict('records')
            return res
        except Exception as e:
            err = Error.handle_exception_info(e)
            err['ext'] = {"func": str(ak_api), "msg": "请求AK接口失败"}
            logger.error(err, 'AK_API_ERR')
            return []

    def stock_sse_summary(self):
        """
        上海证券交易所-股票数据总貌
        :return: dict
        [{'项目': '流通股本', '股票': '47461.19', '主板': '45699.24', '科创板': '1761.95'}, {'项目': '总市值', '股票': '543498.67', '主板': '474558.45', '科创板': '68940.22'}, {'项目': '平市盈率', '股票': '14.08', '主板': '13.03', '科创板': '49.41'}, {'项目': '上市公司', '股票': '2288', '主板': '1700', '科创板': '588'}, {'项目': '上市股票', '股票': '2327', '主板': : '1739', '科创板': '588'}, {'项目': '流通市值', '股票': '512152.49', '主板': '457876.08', '科创板': '54276.4'}, {'项目': '报告时间', '股票': '20250624', '主板': '20250624', '科创板: '20250624'}, {'项目': '总股本', '股票': '50047.99', '主板': '47773.08', '科创板': '2274.91'}]
        """
        return self._formatter(lambda: ak.stock_sse_summary())

    def stock_szse_summary(self, date):
        """
        深圳证券交易所-市场总貌-证券类别统计
        :param date: 统计日期
        :return: dict
        [{'证券类别': '股票', '数量': 2908, '成交金额': 657710206000.65, '总市值': 33334382473576.34, '流通市值': 28473229932057.27}, {'证券类别': '主板A股', '数量': 1487, '成交金额': 330886373247.27, '总市值': 20439356621083.18, '流通市值': 18562801698627.76}, {'证券类别': '主板B股', '数量': 39, '成交金额': 62256476.56, '总市值': 47884754985.1, '流通市值': 47758167359.44}, {'证券类别': '创业板A股', '数量': 1382, '成交金额': 326761576276.82, '总市值': 12847141097508.06, '流通市值': 9862670066070.07}, {'证券类别': '基金', '数量': 802, '成交金 额': 70006219671.82, '总市值': 1208914190544.68, '流通市值': 1175671779953.54}, {'证券类别': 'ETF', '数量': 492, '成交金额': 64440121569.63, '总市值': 1106500396248.3, '流通市值': 1106500396248.3}, {'证券类别': 'LOF', '数量': 287, '成交金额': 5384965921.91, '总市值': 34820081281.88, '流通市值': 34820081281.88}, {'证券类别': '封闭式基金', '数量': 1, '成交金额: 26736110.5, '总市值': 1482829821.4, '流通市值': 1482829821.4}, {'证券类别': '基础设施基金', '数量': 22, '成交金额': 154396069.76, '总市值': 66110883193.08, '流通市值': 328684726601.94}, {'证券类别': '债券', '数量': 15834, '成交金额': 302379308501.18, '总市值': nan, '流通市值': nan}, {'证券类别': '债券现券', '数量': 15135, '成交金额': 55233287738.78, '总市 值': 88968903532318.27, '流通市值': 2987831184356.69}, {'证券类别': '债券回购', '数量': 27, '成交金额': 246293036018.0, '总市值': nan, '流通市值': nan}, {'证券类别': 'ABS', '数量': 672, '成交金额': 852984744.4, '总市值': 456963948198.19, '流通市值': 456963948198.19}, {'证券类别': '期权', '数量': 514, '成交金额': 357365220.73, '总市值': nan, '流通市值': nan}]
        """
        return self._formatter(lambda: ak.stock_szse_summary(date=date))

    def stock_info_a_code_name(self):
        """
        沪深京 A 股股票代码和股票简称数据
        :return: dict
        [{'code': '000001', 'name': '平安银行'}, {'code': '920819', 'name': '颖泰生物'}]
        """
        return self._formatter(lambda: ak.stock_info_a_code_name())

    def stock_individual_info_em(self, code):
        """
        东方财富-个股-股票信息
        无法查询退市股票
        :param code: 股票代码
        :return: dict
        [{'item': '最新', 'value': 12.89}, {'item': '股票代码', 'value': '603777'}, {'item': '股票简称', 'value': '来伊份'}, {'item': '总股本', 'value': 334424166.0}, {'item': '流通股', 'value': 334424166.0}, {'item': '总市值', 'value': 4310727499.74}, {'item': '流通市值', 'value': 4310727499.74}, {'item': '行业', 'value': '食品饮料'}, {'item': '上市时间', 'value': 20161012}]
        """
        return self._formatter(lambda: ak.stock_individual_info_em(code))

    def stock_individual_basic_info_xq(self, symbol):
        """
        雪球财经-个股-公司概况-公司简介
        可以查询退市股票
        :param symbol: 股票代码（带前缀）
        :return: dict
        [{'item': 'org_id', 'value': 'T000058472'}, {'item': 'org_name_cn', 'value': '上海来伊份股份有限公司'}, {'item': 'org_short_name_cn', 'value': '来伊份'}, {'item': 'org_name_en', 'value': 'Shanghai Laiyifen Co.,Ltd.'}, {'item': 'org_short_name_en', 'value': 'LYFEN'}, {'item': 'main_operation_business', 'value': '自主品牌的休闲食品连锁经营。'}, {'item': 'operating_scope', 'value': '\u3000\u3000食品流通，餐饮服务，食用农产品（不含生猪产品、牛羊肉品）、花卉、工艺礼品、电子产品、通讯器材、体育用品、文具用品、日用百货、汽摩配件、化妆品、玩 具、金银饰品、珠宝饰品、化工产品（不含危险化学品）、电脑及配件、通信设备及相关产品的批发、零售，销售计算机配件及相关智能卡，电子商务（不得从事增值电信、金融业务），仓储（除危险品）企业投资与资产管理、企业管理咨询，计算机网络系统开发、软件开发设计，商务咨询、从事货物及技术的进出口业务，包装服务，票务代理，从事通信设备领域内的技术服务，自有房屋租赁，供应链管管，道路货物运输，国内货运代理，国际海上、国际陆路、国际航空货运代理，以服务外包方式从事计算机数据处理，附设分支机构。【依法须经批准的项目，经相关部门批准后方可开展经营活动】'}, {' 'item': 'district_encode', 'value': '310117'}, {'item': 'org_cn_introduction', 'value': '上海来伊份股份有限公司的主营业务是自主品牌的休闲食品连锁经营。公司的主要产品是坚果炒货及豆制、肉制品及水产品、糖果蜜饯及果蔬、糕点及膨化食品。2024年，公司荣获多项国家级、省部级荣誉奖项，包括中国上市公司成长百强、中国轻工业百强以及北京市多个百强榜单，获中国缝制机械协会40 0周年功勋企业奖，此外，公司产品也荣获了中国轻工业联合会科技进步二等奖，浙江首版次软件产品，浙江省2024年度机器人典型应用等多项荣誉奖项。'}, {'item': 'legal_representative', 'value': '郁瑞芬'}, {'item': 'general_manager', 'value': '郁瑞芬'}, {'item': 'secretary', 'value': '林云'}, {'item': 'established_date', 'value': 1025539200000}, {'item': 'reg_asset', 'value': 334424165.99999994}, {'item': 'staff_num', 'value': 4590}, {'item': 'telephone', 'value': '86-21-51760952'}, {'item': 'postcode', 'value': '200235'}, {'item': 'fax', 'value': '86-21-51760955'}, {'item': 'email', 'value': 'corporate@laiyifen.com'}, {'item': 'org_website', 'value': 'www.laiyifen.com'}, {'item': 'reg_address_cn', 'value': '上海市松江区九亭 镇久富路300号'}, {'item': 'reg_address_en', 'value': None}, {'item': 'office_address_cn', 'value': '上海市徐汇区古宜路90号来伊份管理总部'}, {'item': 'office_address_en', 'value': None}, {'item': 'currency_encode', 'value': '019001'}, {'item': 'currency', 'value': 'CNY'}, {'item': 'listed_date', 'value': 1476201600000}, {'item': 'provincial_name', 'value': ' 上海市'}, {'item': 'actual_controller', 'value': '施永雷 (42.37%)，郁瑞芬 (17.76%)，施辉 (2.66%)'}, {'item': 'classi_name', 'value': '民营企业'}, {'item': 'pre_name_cn', 'value': None}, {'item': 'chairman', 'value': '施永雷'}, {'item': 'executives_nums', 'value': 16}, {'item': 'actual_issue_vol', 'value': 60000000.0}, {'item': 'issue_price', 'value': 11.67}, {'item': 'actual_rc_net_amt', 'value': 660211000.0}, {'item': 'pe_after_issuing', 'value': 22.99}, {'item': 'online_success_rate_of_issue', 'value': 0.04604996}, {'item': 'affiliate_industry', 'value': {'ind_code': 'BK0034', 'ind_name': '食品加工制造'}}]
        """
        return self._formatter(lambda: ak.stock_individual_basic_info_xq(symbol))

    def stock_info_sh_delist(self):
        """
        上海证券交易所暂停/终止上市股票
        :return: dict
        [{'公司代码': '900956', '公司简称': '东贝Ｂ股', '上市日期': datetime.date(1999, 7, 15), '暂停上市日期': datetime.date(2020, 11, 23)}]]
        """
        return self._formatter(lambda: ak.stock_info_sh_delist())

    def stock_info_sz_delist(self):
        """
        深证证券交易所终止/暂停上市股票
        :return: dict
        [{'证券代码': '300799', '证券简称': '左江退', '上市日期': datetime.date(2019, 10, 29), '终止上市日期': datetime.date(2024, 7, 29)}]]
        """
        return self._formatter(lambda: ak.stock_info_sz_delist())

    def stock_board_concept_name_ths(self):
        """
        同花顺的所有概念名称
        :return: dict
        [{'name': '维生素', 'code': '309135'}, {'name': '财税数字化', 'code': '309134'}]
        """
        return self._formatter(lambda: ak.stock_board_concept_name_ths())

    def stock_board_concept_name_em(self):
        """
        东方财富-概念板块的所有概念代码
        :return: dict
        [{'排名': 433, '板块名称': '草甘膦', '板块代码': 'BK0950', '最新价': 1520.91, '涨跌额': -14.17, '涨跌幅': -0.92, '总市值': 158110358000, '换手率': 1.31, '上涨家数': 5, '下跌家数': 7, '领涨股票': '兴发集团', '领涨股票-涨跌幅': 0.59}, {'排名': 434, '板块名称': '肝素概念', '板块代码': 'BK0944', '最新价': 946.35, '涨跌额': -9.54, '涨跌幅': -1.0, '总市值': 230431646000, '换手率': 2.02, '上涨家数': 4, '下跌家数': 9, '领涨股票': '华润双鹤', '领涨股票-涨跌幅': 0.43}, {'排名': 435, '板块名称': '油气设服', '板 块代码': 'BK0606', '最新价': 1846.64, '涨跌额': -18.85, '涨跌幅': -1.01, '总市值': 1776834784000, '换手率': 2.69, '上涨家数': 22, '下跌家数': 25, '领涨股票': '海锅股份', '领涨股票-涨跌幅': 3.35}]
        """
        return self._formatter(lambda: ak.stock_board_concept_name_em())

