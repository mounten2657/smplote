from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GPLConceptModel(MysqlBaseModel):
    """
    股票概念板块表
        - id - int(11) - 自增主键
        - concept_code - varchar(20) - 概念板块code
        - concept_name - varchar(64) - 概念板块名称
        - concept_type - varchar(8) - 概念来源(THS:同花顺|EM:东方财富|XQ:雪球)
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
            "concept_code": data.get('concept_code', ''),
            "concept_name": data.get('concept_name', ''),
            "concept_type": data.get('concept_type', ''),
        }
        return self.insert(insert_data)

    def update_concept(self, pid, data):
        """更新股票概念"""
        return self.update({'id': pid}, data)

    def get_concept(self, concept_code, concept_type):
        """获取股票概念"""
        return self.where({'concept_code': concept_code, 'concept_type': concept_type}).first()
