from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class WechatApiLogModel(MysqlBaseModel):
    """
    微信接口日志表
        - id - bigint - 主键ID
        - app_key - varchar(4) - 应用账户：a1|a2
        - uri - varchar(64) - AI类型
        - biz_code - varchar(64) - 业务码
        - h_event - varchar(64) - 自定义字段，多为事件
        - h_value - varchar(64) - 自定义字段，多为某值
        - request_params - longtext - 请求参数
        - process_params - longtext - 处理参数
        - response_result - longtext - 返回结果
        - is_succeed - tinyint(1) - 是否成功(0否1是)
        - aid - bigint - AI聊天记录ID
        - response_time - int - 响应耗时(ms)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_api_log'

    def add_log(self, app_key, method, uri, body, biz_code=''):
        """日志数据入库"""
        body = body if body else {}
        insert_data = {
            "app_key": app_key,
            "uri": uri,
            "biz_code": biz_code,
            "h_event": method,
            "h_value": Attr.get_by_point(body, 'MsgItem.0.ToUserName', body.get('ToUserName', '')),
            "request_params": body,
            "aid": int(body.get('aid', 0)),
            "process_params": {},
            "response_result": {},
        }
        return self.insert(insert_data)

    def update_log(self, pid, data):
        """更新日志数据"""
        return self.update({'id': pid}, data)
