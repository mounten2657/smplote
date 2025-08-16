from tool.core import Attr


class EmDataFormatter:

    def formate_fn_dupont(self, data):
        """
        格式化杜邦分析数据
        :param data: 源数据
        :return: 格式化数据
        """
        ret = [{
            'date': d['REPORT_DATE'][:10],
            'notice_date': d['NOTICE_DATE'][:10],  # 公示日期
            'data': {
                'roe_jq': {
                    'des': '净资产收益率(加权)(%)',
                    'val': Attr.get(d, 'ROE', 0.0),
                    'sub': []
                },
                'roe': {
                    'des': '净资产收益率(%)',  # = 总资产净利率 * 权益乘数
                    'val': Attr.get(d, 'JROA', 0.0) * Attr.get(d, 'EQUITY_MULTIPLIER', 0.0),
                    'sub': [
                        {
                            'des': '总资产净利率(%)',  # = 营业净利润率 * 总资产周转率
                            'val': Attr.get(d, 'JROA', 0.0),
                            'sub': [
                                {
                                    'des': '营业净利润率(%)',  # = 净利润 / 营业总收入
                                    'val': Attr.get(d, 'SALE_NPR', 0.0),
                                    'sub': [
                                        {
                                            'des': '净利润(元)',  # = 收入总额 - 成本总额
                                            'val': Attr.get(d, 'NETPROFIT', 0.0),
                                            'sub': [
                                                {
                                                    'des': '收入总额(元)',
                                                    'val': Attr.get(d, 'TOTAL_INCOME', 0.0),
                                                    'sub': [
                                                        {
                                                            'des': '营业总收入(元)',
                                                            'val': Attr.get(d, 'TOTAL_OPERATE_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '投资收益(元)',
                                                            'val': Attr.get(d, 'INVEST_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '公允价值变动收益(元)',  # POLICY_BONUS_EXPENSE
                                                            'val': Attr.get(d, 'FAIRVALUE_CHANGE_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '资产处置收益(元)',
                                                            'val': Attr.get(d, 'ASSET_DISPOSAL_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '汇兑收益(元)',
                                                            'val': Attr.get(d, 'EXCHANGE_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                    ]
                                                },
                                                {
                                                    'des': '成本总额(元)',
                                                    'val': Attr.get(d, 'TOTAL_COST', 0.0),
                                                    'sub': [
                                                        {
                                                            'des': '营业成本(元)',
                                                            'val': Attr.get(d, 'OPERATE_COST', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '税金及附加(元)',
                                                            'val': Attr.get(d, 'OPERATE_TAX_ADD', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '所得税费用(元)',
                                                            'val': Attr.get(d, 'INCOME_TAX', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '资产减值损失(元)',
                                                            'val': Attr.get(d, 'ASSET_IMPAIRMENT_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '信用减值损失(元)',
                                                            'val': Attr.get(d, 'CREDIT_IMPAIRMENT_INCOME', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '营业外支出(元)',
                                                            'val': Attr.get(d, 'NONBUSINESS_EXPENSE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '期间费用(元)',
                                                            'val': Attr.get(d, 'TOTAL_EXPENSE', 0.0),
                                                            'sub': [
                                                                {
                                                                    'des': '财务费用(元)',
                                                                    'val': Attr.get(d, 'FINANCE_EXPENSE', 0.0),
                                                                    'sub': []
                                                                },
                                                                {
                                                                    'des': '销售费用(元)',
                                                                    'val': Attr.get(d, 'SALE_EXPENSE', 0.0),
                                                                    'sub': []
                                                                },
                                                                {
                                                                    'des': '管理费用(元)',
                                                                    'val': Attr.get(d, 'MANAGE_EXPENSE', 0.0),
                                                                    'sub': []
                                                                },
                                                                {
                                                                    'des': '研发费用(元)',
                                                                    'val': Attr.get(d, 'RESEARCH_EXPENSE', 0.0),
                                                                    'sub': []
                                                                },
                                                            ]
                                                        },
                                                    ]
                                                },
                                            ]
                                        },
                                        {
                                            'des': '营业总收入(元)',
                                            'val': Attr.get(d, 'TOTAL_OPERATE_INCOME', 0.0),
                                            'sub': []
                                        },
                                    ]
                                },
                                {
                                    'des': '总资产周转率(次)',
                                    'val': Attr.get(d, 'TOTAL_ASSETS_TR', 0.0),
                                    'sub': []
                                },
                            ]
                        },
                        {
                            'des': '归属母公司股东的净利润占比(%)',
                            'val': Attr.get(d, 'PARENT_NETPROFIT_RATIO', 0.0),
                            'sub': []
                        },
                        {
                            'des': '权益乘数',  # = 1 / (1 - 资产负债率)
                            'val': Attr.get(d, 'EQUITY_MULTIPLIER', 0.0),
                            'sub': [
                                {
                                    'des': '资产负债率(%)',  # = 负债总额 / 资产总额
                                    'val': Attr.get(d, 'DEBT_ASSET_RATIO', 0.0),
                                    'sub': [
                                        {
                                            'des': '负债总额(元)',
                                            'val': Attr.get(d, 'TOTAL_LIABILITIES', 0.0),
                                            'sub': []
                                        },
                                        {
                                            'des': '资产总额(元)',  # = 流动资产 + 非流动资产
                                            'val': Attr.get(d, 'TOTAL_ASSETS', 0.0),
                                            'sub': [
                                                {
                                                    'des': '流动资产(元)',
                                                    'val': Attr.get(d, 'TOTAL_CURRENT_ASSETS', 0.0),
                                                    'sub': [
                                                        {
                                                            'des': '货币资金(元)',
                                                            'val': Attr.get(d, 'MONETARYFUNDS', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '交易性金融资产(元)',
                                                            'val': Attr.get(d, 'TRADE_FINASSET', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '应收票据(元)',
                                                            'val': Attr.get(d, 'NOTE_RECE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '应收账款(元)',
                                                            'val': Attr.get(d, 'ACCOUNTS_RECE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '应收账款融资(元)',
                                                            'val': Attr.get(d, 'FINANCE_RECE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '其它应收款(元)',
                                                            'val': Attr.get(d, 'OTHER_RECE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '存货(元)',
                                                            'val': Attr.get(d, 'INVENTORY', 0.0),
                                                            'sub': []
                                                        },
                                                    ]
                                                },
                                                {
                                                    'des': '非流动资产(元)',
                                                    'val': Attr.get(d, 'TOTAL_NONCURRENT_ASSETS', 0.0),
                                                    'sub': [
                                                        {
                                                            'des': '债券投资(元)',
                                                            'val': Attr.get(d, 'CREDITOR_INVEST', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '其他债权投资(元)',
                                                            'val': Attr.get(d, 'OTHER_CREDITOR_INVEST', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '其他权益工具投资(元)',
                                                            'val': Attr.get(d, 'OTHER_EQUITY_INVEST', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '长期应收款(元)',
                                                            'val': Attr.get(d, 'LONG_RECE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '长期股权投资(元)',
                                                            'val': Attr.get(d, 'LONG_EQUITY_INVEST', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '投资性房地产(元)',
                                                            'val': Attr.get(d, 'INVEST_REALESTATE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '固定资产(元)',
                                                            'val': Attr.get(d, 'FIXED_ASSET', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '在建工程(元)',
                                                            'val': Attr.get(d, 'CIP', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '使用权资产(元)',
                                                            'val': Attr.get(d, 'USERIGHT_ASSET', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '无形资产(元)',
                                                            'val': Attr.get(d, 'INTANGIBLE_ASSET', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '开发支出(元)',
                                                            'val': Attr.get(d, 'DEVELOP_EXPENSE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '商誉(元)',
                                                            'val': Attr.get(d, 'GOODWILL', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '长期待摊费用(元)',
                                                            'val': Attr.get(d, 'LONG_PREPAID_EXPENSE', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '递延所得税资产(元)',
                                                            'val': Attr.get(d, 'DEFER_TAX_ASSET', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '可供出售金融资产(元)',
                                                            'val': Attr.get(d, 'AVAILABLE_SALE_FINASSET', 0.0),
                                                            'sub': []
                                                        },
                                                        {
                                                            'des': '持有至到期投资(元)',
                                                            'val': Attr.get(d, 'HOLD_MATURITY_INVEST', 0.0),
                                                            'sub': []
                                                        },
                                                    ]
                                                },
                                            ]
                                        },
                                    ]
                                },
                            ]
                        },
                    ]
                },
            },
        } for d in data]
        return ret


