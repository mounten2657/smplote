from flask import request
from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Http, Attr


@Ins.singleton
class CallbackQueueModel(MysqlBaseModel):
    """
    回调队列表
    ```
    DROP TABLE IF EXISTS smp_callback_queue;
    CREATE TABLE `smp_callback_queue` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `callback_type` varchar(32) NOT NULL DEFAULT '' COMMENT '回调类型: gewechat|qyapi|gitee',
      `source_url` varchar(512) NOT NULL DEFAULT '' COMMENT '源地址',
      `route` varchar(64) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '路由地址',
      `ip` varchar(64) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT 'ip地址',
      `ua` varchar(128) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT 'User-Agent',
      `method` varchar(10) NOT NULL DEFAULT 'POST' COMMENT '请求方式',
      `params` longtext NOT NULL COMMENT '请求参数',
      `headers` text NOT NULL COMMENT '请求头',
      `h_event` varchar(128) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '自定义字段，多为事件',
      `h_value` varchar(128) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '自定义字段，多为某值',
      `is_processed` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否处理(0否1是)',
      `is_succeed` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否成功(0否1是)',
      `process_params` text NOT NULL COMMENT '处理参数',
      `process_result` text NOT NULL COMMENT '处理结果',
      `retry_count` int(11) NOT NULL DEFAULT 0 COMMENT '重试次数',
      `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
      `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
      PRIMARY KEY (`id`),
      KEY `idx_type_status` (`callback_type`, `is_processed`, `is_succeed`)
    ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='回调队列表';
    ```
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
        return self.update({'id': pid}, {'is_processed': is_processed})

    def set_succeed(self, pid, is_succeed=1):
        return self.update({'id': pid}, {'is_succeed': is_succeed})

    def update_process(self, pid, data):
        return self.update({'id': pid}, data)

    def get_unprocessed_list(self, callback_type):
        condition = {'callback_type': callback_type, 'is_processed': 0}
        return self.where(condition).get()


