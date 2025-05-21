from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatApiLog(MysqlBaseModel):
    """
    微信接口日志表
    ```
    DROP TABLE IF EXISTS smp_wechat_api_log;
    CREATE TABLE `smp_wechat_api_log` (
        `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
        `uri` varchar(64) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT 'AI类型',
        `biz_code` varchar(64) COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '业务码',
        `h_event` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '自定义字段，多为事件',
        `h_value` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL DEFAULT '' COMMENT '自定义字段，多为某值',
        `request_params` longtext COLLATE utf8mb4_general_ci NOT NULL COMMENT '请求参数',
        `process_params` longtext COLLATE utf8mb4_general_ci NOT NULL COMMENT '处理参数',
        `response_result` longtext COLLATE utf8mb4_general_ci NOT NULL COMMENT '返回结果',
        `is_succeed` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否成功(0否1是)',
        `response_time` int NOT NULL DEFAULT '0' COMMENT '响应耗时(ms)',
        `create_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
        `update_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
        PRIMARY KEY (`id`),
        KEY `idx_uri` (`uri`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='微信接口日志表';
    ```
    """

    _table = 'wechat_api_log'

    def add_log(self, method, uri, body, biz_code=''):
        """日志数据入库"""
        insert_data = {
            "uri": uri,
            "biz_code": biz_code,
            "h_event": method,
            "request_params": body if body else {},
            "process_params": {},
            "response_result": {},
        }
        return self.insert(insert_data)

    def update_log(self, pid, data):
        """更新日志数据"""
        return self.update({'id': pid}, data)

