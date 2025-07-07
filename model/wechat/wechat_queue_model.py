from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Time


@Ins.singleton
class WechatQueueModel(MysqlBaseModel):
    """
    微信队列表
        - id - bigint(20) - 主键ID
        - callback_type - varchar(32) - 回调类型: wechatpad
        - app_key - varchar(4) - 应用账户：a1|a2
        - params - longtext - 请求参数
        - h_event - varchar(64) - 自定义字段，多为事件
        - h_value - varchar(64) - 自定义字段，多为某值
        - is_processed - tinyint(1) - 是否处理(0否1是)
        - is_succeed - tinyint(1) - 是否成功(0否1是)
        - process_params - text - 处理参数
        - process_result - text - 处理结果
        - retry_count - int(11) - 重试次数
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_queue'

    def add_queue(self, app_key, params, callback_type='wechatpad', process_params=None):
        """数据入队列"""
        insert_data = {
            "callback_type": callback_type,
            "app_key": app_key,
            "params": params,
            "h_event": Time.dft(params.get('message', {}).get('create_time', 0)),
            "h_value": params.get('message', {}).get('new_msg_id', 0),
            "process_params": process_params if process_params else {},
            "process_result": {},
        }
        return self.insert(insert_data)

    def set_processed(self, pid, is_processed=1):
        """更新为已受理"""
        return self.update({'id': pid}, {'is_processed': is_processed})

    def set_retry_count(self, pid, retry_count=1):
        """更新重试次数 - 也可以引申为业务的标志位"""
        return self.update({'id': pid}, {'retry_count': retry_count})

    def update_process(self, pid, data):
        """更新处理数据"""
        info = self.where({"id": pid}).first()
        if not info:
            return False
        if data.get('process_params'):
            info['process_params'] = info['process_params'] if info['process_params'] else {}
            info['process_params'].update(data['process_params'])
            data['process_params'] = info['process_params']
        return self.update({'id': pid}, data)

    def get_list_by_id(self, id_list, callback_type='wechatpad'):
        """获取特定ID组的队列"""
        if -1 == int(id_list[0]):
            # 处理未成功的数据
            where = {
                "callback_type": callback_type,
                "is_processed": 1,
                "is_succeed": 0,
                "create_at": {"opt": ">=", "val": Time.date("%Y-%m-%d 00:00:00")}
            }
            return self.where(where).get()
        return self.where_in('id', id_list).where({'callback_type': callback_type}).get()

    def get_by_msg_id(self, msg_id):
        """wechatpad 专用 - 通过消息ID获取，主要用于消息去重"""
        condition = {'callback_type': 'wechatpad', 'h_value': msg_id}
        return self.where(condition).first()
