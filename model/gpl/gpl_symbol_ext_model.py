from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLSymbolExtModel(MysqlBaseModel):
    """
    股票额外信息表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - biz_type - varchar(16) - 业务类型
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - text - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_symbol_ext'

    def add_ext(self, data):
        """股票额外信息入库"""
        data = data if data else {}
        e_key = data.get('e_key', '')
        if not data or not e_key:
            return 0
        insert_data = {
            "symbol": data.get('symbol', ''),
            "biz_type": data.get('biz_type', ''),
            "e_key": data.get('e_key', ''),
            "e_des": data.get('e_des', ''),
            "e_val": data.get('e_val', ''),
        }
        return self.insert(insert_data)

    def update_ext(self, pid, data):
        """更新股票额外信息"""
        return self.update({'id': pid}, data)

    def get_ext_list(self, symbol, biz_type):
        """获取股票额外信息列表"""
        a_list = self.where({'symbol': symbol, 'biz_type': biz_type}).get()
        return Attr.kv_list_to_dict(a_list)

    def get_ext(self, symbol, biz_type, e_key):
        """获取股票额外信息"""
        return self.where({'symbol': symbol, 'biz_type': biz_type, 'e_key': e_key}).first()
