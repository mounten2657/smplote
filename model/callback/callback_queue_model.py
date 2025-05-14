from flask import request
from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class CallbackQueueModel(MysqlBaseModel):
    """
    回调队列表
    ```
    CREATE TABLE `smp_callback_queue` (
      `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `callback_type` varchar(32) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '回调类型: gewechat|qyapi|gitee',
      `source_url` varchar(512) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '源地址',
      `method` varchar(10) COLLATE utf8mb4_general_ci NOT NULL DEFAULT 'POST' COMMENT '请求方式',
      `params` longtext COLLATE utf8mb4_general_ci NOT NULL COMMENT '请求参数',
      `headers` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '请求头',
      `is_processed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否处理(0否1是)',
      `is_succeed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否成功(0否1是)',
      `process_params` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '处理参数',
      `process_result` text COLLATE utf8mb4_general_ci NOT NULL COMMENT '处理结果',
      `retry_count` int NOT NULL DEFAULT '0' COMMENT '重试次数',
      `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
      `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
      PRIMARY KEY (`id`),
      KEY `idx_type_status` (`callback_type`,`is_processed`,`is_succeed`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='回调队列表';
    ```
    """

    _table = 'callback_queue'

    def add_queue(self, callback_type, params, headers=None, process_params=None):
        """数据入队列"""
        insert_data = {
            "callback_type": callback_type,
            "source_url": request.url,
            "method": request.method,
            "params": params,
            "headers": headers if headers else {},
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


