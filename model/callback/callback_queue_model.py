from flask import request
from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Http, Attr, Config, Time


@Ins.singleton
class CallbackQueueModel(MysqlBaseModel):
    """
    回调队列表
        - id - bigint(20) - 主键ID
        - callback_type - varchar(32) - 回调类型: qyapi|gitee
        - source_url - varchar(512) - 源地址
        - route - varchar(64) - 路由地址
        - ip - varchar(64) - ip地址
        - ua - varchar(128) - User-Agent
        - method - varchar(10) - 请求方式
        - params - longtext - 请求参数
        - headers - text - 请求头
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

    _table = 'callback_queue'

    def add_queue(self, callback_type, params, process_params=None, custom_params=None):
        """数据入队列"""
        headers = custom = Http.get_request_headers()
        custom.update(custom_params if custom_params else {})
        # 先尝试有没有直接的键值，没有再看有没有指定键名，再没有，才读取默认的键名从header头中获取
        h_event = custom.get('h_event', Attr.get_value_by_key_like(custom, custom.get('h_event_key', 'event')))
        h_value = custom.get('h_value', Attr.get_value_by_key_like(custom, custom.get('h_value_key', 'timestamp')))
        insert_data = {
            "callback_type": callback_type,
            "source_url": request.url,
            "route": Http.get_request_route(),
            "ip": Http.get_client_ip(),
            "ua": headers.get('User-Agent', ''),
            "method": request.method,
            "params": params,
            "headers": headers,
            "h_event": h_event,
            "h_value": h_value,
            "process_params": process_params if process_params else {},
            "process_result": {},
        }
        return self.insert(insert_data)

    def set_processed(self, pid, is_processed=1):
        """更新为已受理"""
        return self.update({'id': pid}, {'is_processed': is_processed})

    def update_process(self, pid, data, is_force=0):
        """更新处理数据"""
        info = self.where({"id": pid}).first()
        if not info:
            return False
        if data.get('process_params') and not is_force:
            info['process_params'] = info['process_params'] if info['process_params'] else {}
            info['process_params'].update(data['process_params'])
            data['process_params'] = info['process_params']
        return self.update({'id': pid}, data)
