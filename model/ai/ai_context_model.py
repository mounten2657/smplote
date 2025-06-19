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

    def add_context(self, context, config):
        """数据入库"""
        insert_data = {
            "chat_id": context['chat_id'],
            "biz_code": context['biz_code'],
            "method_name": context['method_name'],
            "ai_type": config['ai_type'],
            "ai_model": config['ai_model'],
            "request_params": context['request_params'],
            "response_result": {},
            "is_succeed": 0,
            "is_summary": context['is_summary'],
            "response_time": 0,
        }
        return self.insert(insert_data)

    def update_context_response(self, pid, response):
        """更新响应结果"""
        return self.update({"id": pid}, response)

    def get_context_info(self, pid):
        """获取上下文信息"""
        return self.where({"id": pid}).first()

    def get_context_list(self, cid, biz_code):
        """获取上下文列表 - 最近5条"""
        return (self.where({"chat_id": cid, "is_summary": 0, "biz_code": biz_code})
                .order('id', 'desc')
                .limit(0, 5)
                .get())

    def get_context_count(self, cid, biz_code):
        """获取对话总条数"""
        return self.get_count({"chat_id": cid, "is_summary": 0, "biz_code": biz_code})
