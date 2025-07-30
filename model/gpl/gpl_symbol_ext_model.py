from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr, Time
from model.gpl.gpl_change_log_model import GPLChangeLogModel


@Ins.singleton
class GPLSymbolExtModel(MysqlBaseModel):
    """
    股票额外信息表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - biz_code - varchar(16) - 业务代码
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - longtext - kv值
        - sid - bigint - 附表主键ID
        - std - date - 附表日期
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_symbol_ext'

    def add_ext(self, data):
        """股票额外信息入库"""
        e_key = Attr.get(data, 'e_key', '')
        if not e_key:
            return 0
        insert_data = {
            "symbol": data.get('symbol', ''),
            "biz_code": data.get('biz_code', ''),
            "e_key": data.get('e_key', ''),
            "e_des": data.get('e_des', ''),
            "e_val": data.get('e_val', ''),
            "sid": data.get('sid', 0),
            "std": data.get('std', Time.date('%Y-%m-%d')),
        }
        return self.insert(insert_data)

    def update_ext(self, pid, symbol, key, data, before=None):
        """更新股票额外信息"""
        u_data = {'e_val': data[key]}
        res = self.update({'id': pid}, u_data)
        # 自动记录变更日志
        if before and len(before) == len(data):
            GPLChangeLogModel().add_change_log(symbol, self.table_name(), data, before)
        return res

    def get_ext_list(self, symbol, biz_code):
        """获取股票额外信息列表"""
        a_list = self.where({'symbol': symbol, 'biz_code': biz_code}).get()
        return Attr.kv_list_to_dict(a_list)

    def get_ext(self, symbol, biz_code, e_key):
        """获取股票额外信息"""
        return self.where({'symbol': symbol, 'biz_code': biz_code, 'e_key': e_key}).first()
