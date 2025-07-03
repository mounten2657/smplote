from model.gpl.gpl_daily_model import GPLDailyModel
from tool.core import Time, Attr


class GPLCalculateService:
    """股票计算类"""

    @staticmethod
    def calc_stock_return(symbol: str, bd: str, bn: int, sd: str, sn: int = 0):
        """
        计算股票收益
            实际收益率 = ((卖出日的后复权价格 / 买入日的后复权价格 - 1) × 卖出比例) × 100%
            实际收益金额 = 买入金额 × 实际收益率 / 100

        :param symbol:  股票代码
        :param str bd: 买入日期 (YYYY-MM-DD)
        :param int bn: 买入数量
        :param str sd: 卖出日期 (YYYY-MM-DD)
        :param int sn: 卖出数量
        :return: dict
        """
        # 从数据库中读取历史数据
        d_list = GPLDailyModel().get_daily(symbol, [bd, sd])
        if not d_list or (d_list and len(d_list) != 2):
            return {}
        buy_info = Attr.select_item_by_where(d_list, {"trade_date": bd}, {})
        sell_info = Attr.select_item_by_where(d_list, {"trade_date": sd}, {})
        buy_price = buy_info.get('f2_close', 0.00)
        sell_price = sell_info.get('f2_close', 0.00)
        # 计算收益
        profile = round((sell_price / buy_price - 1) * (sn / bn) * 100)
        money = round(bn * buy_price * profile / 100)
        hold_days = int((Time.tfd(sd, '%Y-%m-%d') - Time.tfd(bd, '%Y-%m-%d')) / 86400)
        # 返回结果
        return {
            'symbol': symbol,
            'buy_date': bd,
            'buy_price': buy_price,
            'buy_num': bn,
            'sell_date': sd,
            'sell_price': sell_price,
            'sell_num': sn,
            'left_num': bn - sn,
            'hold_days': hold_days,
            'profit': profile,
            'money': money
        }
