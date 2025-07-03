from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLSymbolTextModel(MysqlBaseModel):
    """
    股票文本信息表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - biz_type - varchar(16) - 业务类型
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - longtext - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_symbol_text'

    def add_text(self, data):
        """股票文本信息入库"""
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

    def update_text(self, pid, data):
        """更新股票文本信息"""
        return self.update({'id': pid}, data)

    def get_text_list(self, symbol_list, biz_type):
        """获取股票文本信息列表"""
        return self.where_in('symbol', symbol_list).where({'biz_type': biz_type}).get()

    def get_text(self, symbol, biz_type, e_key):
        """获取股票文本信息"""
        return self.where({'symbol': symbol, 'biz_type': biz_type, 'e_key': e_key}).first()
