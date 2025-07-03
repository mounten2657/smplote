from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GPLConceptModel(MysqlBaseModel):
    """
    股票概念板块表
        - id - int(11) - 自增主键
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - source_type - varchar(8) - 概念来源(EM:东方财富|XQ:雪球|THS:同花顺)
        - concept_code - varchar(20) - 概念板块code
        - concept_name - varchar(64) - 概念板块名称
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_concept'

    def add_concept(self, data):
        """股票概念入库"""
        data = data if data else {}
        concept_code = data.get('concept_code', '')
        if not data or not concept_code:
            return 0
        insert_data = {
            "symbol": data.get('symbol', ''),
            "source_type": data.get('source_type', ''),
            "concept_code": data.get('concept_code', ''),
            "concept_name": data.get('concept_name', ''),
        }
        return self.insert(insert_data)

    def update_concept(self, pid, data):
        """更新股票概念"""
        return self.update({'id': pid}, data)

    def del_concept(self, source_type, code_list):
        """删除固定板块"""
        c_str = "('" + "','".join(code_list) + "')"
        return self.delete({'source_type': source_type, 'concept_code': {'opt': 'in', 'val': c_str}})

    def get_concept_list(self, symbol_list, source_type):
        """获取股票常量列表"""
        return self.where_in('symbol', symbol_list).where({'source_type': source_type}).get()

    def get_concept(self, symbol, source_type, concept_code):
        """获取股票概念"""
        return self.where({'symbol': symbol, 'source_type': source_type, 'concept_code': concept_code}).first()
