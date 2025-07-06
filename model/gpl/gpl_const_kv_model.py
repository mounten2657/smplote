from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLConstKvModel(MysqlBaseModel):
    """
    股票常量键值表
        - id - bigint(20) - 自增主键
        - biz_type - varchar(16) - kv业务类型
        - e_key - varchar(32) - kv键
        - e_des - varchar(128) - kv描述
        - e_val - text - kv值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_const_kv'

    def add_const(self, data):
        """股票常量入库"""
        data = data if data else {}
        biz_type = data.get('biz_type', '')
        if not data or not biz_type:
            return 0
        insert_data = {
            "biz_type": data.get('biz_type', ''),
            "e_key": data.get('e_key', ''),
            "e_des": data.get('e_des', ''),
            "e_val": data.get('e_val', ''),
        }
        return self.insert(insert_data)

    def update_const(self, pid, data):
        """更新股票常量"""
        return self.update({'id': pid}, data)

    def get_const_list(self, biz_type):
        """获取股票常量列表"""
        a_list = self.where({'biz_type': biz_type}).get()
        return Attr.kv_list_to_dict(a_list)

    def get_const_em_yesterday(self):
        """获取股票东财昨日板块列表"""
        return self.where({'biz_type': 'EM_CONCEPT', 'e_val': {'opt': 'like', 'val': '昨日%'}}).get()

    def get_const(self, biz_type, e_key):
        """获取股票常量"""
        return self.where({'biz_type': biz_type, 'e_key': e_key}).first()
