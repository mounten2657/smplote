from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLChangeLogModel(MysqlBaseModel):
    """
    股票变更日志表
        - id - bigint(20) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - cl_tab - varchar(32) - 变更表名
        - cl_key - varchar(32) - 变更字段
        - cl_time - datetime - 变更时间
        - cl_md5 - varchar(32) - 变更md5
        - cl_bef - text - 变更前的值
        - cl_aft - text - 变更后的值
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_change_log'

    def add_change_log(self, data, before, after):
        """股票概念入库"""
        data = data if data else {}
        cl_tab = data.get('cl_tab', '')
        if not data or not cl_tab or len(before) != len(after):
            return 0
        insert_list = []
        for k, v in before.items():
            insert_data = {
                "symbol": data.get('symbol', ''),
                "cl_tab": data.get('cl_tab', ''),
                "cl_key": k,
                "cl_time": data.get('cl_time', ''),
                "cl_md5": data.get('cl_md5', ''),
                "cl_bef": v,
                "cl_aft": after[k],
            }
            insert_list.append(insert_data)
        return self.insert(insert_list)

    def get_change_log(self, symbol, cl_tab, cl_key):
        """获取股票变更日志"""
        return self.where({'symbol': symbol, 'cl_tab': cl_tab, 'cl_key': cl_key}).get()
