from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLSymbolTextModel(MysqlBaseModel):
    """
    股票文本信息表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - biz_code - varchar(16) - 业务代码
        - e_key - varchar(32) - kv键
        - e_des - varchar(255) - kv描述
        - e_val - longtext - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_symbol_text'

    def add_text(self, data, check_exist=False):
        """股票文本信息入库"""
        data = data if data else {}
        e_key = data.get('e_key', '')
        if not data or not e_key:
            return 0
        if check_exist:
            info = self.get_text(data.get('symbol', ''), data.get('biz_code', ''), data.get('e_key', ''))
            if info:
                return info['id']
        insert_data = {
            "symbol": data.get('symbol', ''),
            "biz_code": data.get('biz_code', ''),
            "e_key": data.get('e_key', ''),
            "e_des": data.get('e_des', ''),
            "e_val": data.get('e_val', ''),
        }
        return self.insert(insert_data)

    def update_text(self, pid, data):
        """更新股票文本信息"""
        return self.update({'id': pid}, data)

    def get_text_list(self, symbol_list, biz_code):
        """获取股票文本信息列表"""
        if len(symbol_list) == 1:
            return self.where({'symbol': symbol_list[0], 'biz_code': biz_code}).get()
        return self.where_in('symbol', symbol_list).where({'biz_code': biz_code}).get()

    def get_text(self, symbol, biz_code, e_key):
        """获取股票文本信息"""
        return self.where({'symbol': symbol, 'biz_code': biz_code, 'e_key': e_key}).first()
