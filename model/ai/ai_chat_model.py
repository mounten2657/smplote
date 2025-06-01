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
        - chat_count - int - 对话次数
        - last_summary - text - 最近一次的总结
        - remark - varchar(255) - 备注
        - extra - text - 额外参数
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'ai_chat'

    def add_chat(self, chat, config):
        """数据入库"""
        insert_data = {
            "biz_code": chat['biz_code'],
            "user_id": chat['user_id'],
            "user_name": chat['user_name'],
            "ai_type": config['ai_type'],
            "ai_model": config['ai_model'],
            "chat_name": chat['chat_name'],
            "chat_count": 0,
            "last_summary": [],
            "remark": "",
            "extra": chat['extra'],
        }
        return self.insert(insert_data)

    def update_chat_summary(self, pid, summary):
        """更新最近总结"""
        return self.update({"id": pid}, summary)

    def get_chat_info(self, uid, biz_code):
        """获取会话信息"""
        return self.where({"user_id": uid, "biz_code": biz_code}).first()
