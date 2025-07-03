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

    def add_season(self, data):
        """股票季度信息入库"""
        data = data if data else {}
        e_key = data.get('e_key', '')
        if not data or not e_key:
            return 0
        insert_data = {
            "symbol": data.get('symbol', ''),
            "season_date": data.get('season_date', ''),
            "biz_type": data.get('biz_type', ''),
            "e_key": data.get('e_key', ''),
            "e_des": data.get('e_des', ''),
            "e_val": data.get('e_val', ''),
        }
        return self.insert(insert_data)

    def update_season(self, pid, data):
        """更新股票季度信息"""
        return self.update({'id': pid}, data)

    def get_season_list(self, symbol, season_date, biz_type):
        """获取股票季度信息列表"""
        a_list = self.where({'symbol': symbol, 'season_date': season_date, 'biz_type': biz_type}).get()
        return Attr.kv_list_to_dict(a_list)

    def get_season(self, symbol, season_date, biz_type, e_key):
        """获取股票季度信息"""
        return self.where({'symbol': symbol, 'season_date': season_date, 'biz_type': biz_type, 'e_key': e_key}).first()
