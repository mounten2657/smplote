from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class AiChatModel(MysqlBaseModel):
    """
    AI对话表
        - id - int - 主键ID
        - biz_code - varchar(32) - 业务code
        - user_id - varchar(64) - 用户ID
        - user_name - varchar(128) - 用户名
        - ai_type - varchar(32) - AI类型
        - ai_model - varchar(64) - AI模型
        - chat_name - varchar(128) - 对话名称
        - last_summary - text - 最近一次的总结
        - response_time - int - 响应耗时(ms)
        - remark - varchar(255) - 备注
        - extra - text - 额外参数
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'ai_chat'
