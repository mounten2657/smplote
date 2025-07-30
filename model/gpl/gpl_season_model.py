from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLSeasonModel(MysqlBaseModel):
    """
    股票季度信息表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - season_date - date - 季度尾日
        - biz_code - varchar(16) - 业务代码
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - longtext - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_season'

    def add_season(self, symbol, date, biz_code, biz_data):
        """股票季度信息入库"""
        if not biz_data or not isinstance(biz_data, dict):
            return 0
        insert_data = {
                "symbol": symbol,
                "season_date": date,
                "biz_code": biz_code,
                "e_key": Attr.get(biz_data, 'key', ''),
                "e_des": Attr.get(biz_data, 'des', ''),
                "e_val": Attr.get(biz_data, 'val', ''),
            }
        return self.insert(insert_data)

    def update_season(self, pid, data):
        """更新股票季度信息"""
        return self.update({'id': pid}, data)

    def get_season_list(self, symbol_list, season_date_list, biz_code, limit = 0):
        """获取股票季度信息列表"""
        db = self.where_in('symbol', symbol_list)
        if season_date_list:
            db = db.where_in('season_date', season_date_list)
        if limit:
            db = db.order('id', 'desc').limit(0, limit)
        a_list = db.where({'biz_code': biz_code}).get()
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

    def get_season_recent(self, symbol, biz_code, e_key=None):
        """获取股票最新季度信息"""
        where = {'symbol': symbol, 'biz_code': biz_code}
        if e_key:
            where['e_key'] = e_key
        return self.where(where).order('season_date', 'desc').first()

    def get_season(self, symbol, season_date, biz_code, e_key=None):
        """获取股票季度信息"""
        where = {'symbol': symbol, 'season_date': season_date, 'biz_code': biz_code}
        if e_key:
            where['e_key'] = e_key
        return self.where(where).first()
