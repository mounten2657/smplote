from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLConstKvModel(MysqlBaseModel):
    """
    股票常量键值表
        - id - bigint(20) - 自增主键
        - biz_code - varchar(16) - 业务代码
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - longtext - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_const_kv'

    def add_const(self, data):
        """股票常量入库"""
        data = data if data else {}
        biz_code = data.get('biz_code', '')
        if not data or not biz_code:
            return 0
        insert_data = {
            "biz_code": data.get('biz_code', ''),
            "e_key": data.get('e_key', ''),
            "e_des": data.get('e_des', ''),
            "e_val": data.get('e_val', ''),
        }
        return self.insert(insert_data)

    def update_const(self, pid, data):
        """更新股票常量"""
        return self.update({'id': pid}, data)

    def get_const_list(self, biz_code):
        """获取股票常量列表"""
        a_list = self.where({'biz_code': biz_code}).get()
        return Attr.kv_list_to_dict(a_list)

    def get_const_em_yesterday(self):
        """获取股票东财昨日板块列表"""
        return self.where({'biz_code': 'EM_CONCEPT', 'e_val': {'opt': 'like', 'val': '昨日%'}}).get()

    def get_const(self, biz_code, e_key):
        """获取股票常量"""
        return self.where({'biz_code': biz_code, 'e_key': e_key}).first()
