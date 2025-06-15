from flask import request
from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Http, Attr, Config, Time


@Ins.singleton
class CallbackQueueModel(MysqlBaseModel):
    """
    回调队列表
        - id - bigint(20) - 主键ID
        - callback_type - varchar(32) - 回调类型: qyapi|gitee|wechatpad
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
        if callback_type == 'wechatpad':
            config = Config.vp_config()
            insert_data = {
                "callback_type": callback_type,
                "source_url": f'ws://{config['ws_host']}:{config['ws_port']}',
                "route": '/ws/GetSyncMsg',
                "ip": '127.0.0.1',
                "ua": 'ws-wechatpad',
                "method": 'COMMAND',
                "params": params,
                "headers": {},
                "h_event": Time.dft(params.get('message', {}).get('create_time', 0)),
                "h_value": params.get('message', {}).get('new_msg_id', 0),
                "process_params": process_params if process_params else {},
                "process_result": {},
            }
        else:
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

    def set_succeed(self, pid, is_succeed=1):
        """更新为已处理成功"""
        return self.update({'id': pid}, {'is_succeed': is_succeed})

    def set_retry_count(self, pid, retry_count=1):
        """更新重试次数 - 也可以引申为业务的标志位"""
        return self.update({'id': pid}, {'retry_count': retry_count})

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

    def get_unprocessed_list(self, callback_type):
        """获取未处理的队列"""
        condition = {'callback_type': callback_type, 'is_processed': 0}
        return self.where(condition).get()

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
        return (self.where(condition)
                .where_in('is_processed', [0, 1])
                .where_in('is_succeed', [0, 1])
                .first())


