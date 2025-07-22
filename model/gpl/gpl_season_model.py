from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLSeasonModel(MysqlBaseModel):
    """
    股票季度信息表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - season_date - date - 季度尾日
        - biz_type - varchar(16) - 业务类型
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - text - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_season'

    def add_season(self, symbol, date, biz_type, biz_data):
        """股票季度信息入库"""
        if not biz_data or not isinstance(biz_data, dict):
            return 0
        insert_data = {
                "symbol": symbol,
                "season_date": date,
                "biz_type": biz_type,
                "e_key": Attr.get(biz_data, 'key', ''),
                "e_des": Attr.get(biz_data, 'des', ''),
                "e_val": Attr.get(biz_data, 'val', ''),
            }
        return self.insert(insert_data)

    def update_season(self, pid, data):
        """更新股票季度信息"""
        return self.update({'id': pid}, data)

    def get_season_list(self, symbol_list, season_date_list, biz_type):
        """获取股票季度信息列表"""
        a_list = (self.where_in('symbol', symbol_list).where_in('season_date', season_date_list)
                  .where({'biz_type': biz_type}).get())
        # return Attr.kv_list_to_dict(a_list)
        if not a_list:
            return {}
        ret = {}
        for d in a_list:
            key = f"{d['symbol']}_{d['season_date']}"
            val = {d['e_key']: d['e_val']}
            if not ret.get(key):
                ret[key] = d | val
            else:
                ret[key] = ret[key] | val
        return ret

    def get_season(self, symbol, season_date, biz_type, e_key=None):
        """获取股票季度信息"""
        e_key = e_key if e_key else str(biz_type).lower()
        return self.where({'symbol': symbol, 'season_date': season_date, 'biz_type': biz_type, 'e_key': e_key}).first()
