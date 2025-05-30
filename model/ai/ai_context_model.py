from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class AiContextModel(MysqlBaseModel):
    """
    AI上下文记录表
        - id - int - 主键ID
        - chat_id - int - 关联对话ID
        - biz_code - varchar(64) - 业务码
        - method_name - varchar(64) - 方法名
        - ai_type - varchar(32) - AI类型
        - ai_model - varchar(64) - AI模型
        - request_params - longtext - 请求参数
        - response_result - text - 返回结果
        - is_succeed - tinyint(1) - 是否成功(0否1是)
        - is_summary - tinyint(1) - 是否总结(0否1是)
        - response_time - int - 响应耗时(ms)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'ai_context'
