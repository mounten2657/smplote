from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatFileModel(MysqlBaseModel):
    """
    微信文件表
        - id - bigint - 主键ID
        - url - varchar(255) - 文件链接
        - fake_path - varchar(255) - 虚拟路径
        - save_path - varchar(255) - 真实路径
        - file_name - varchar(255) - 文件名
        - file_ext - varchar(8) - 文件后缀
        - biz_code - varchar(32) - 业务代码
        - file_md5 - varchar(32) - 文件md5
        - file_size - int - 文件大小(byte)
        - que_id - bigint - 队列ID
        - msg_id - bigint - 消息ID
        - s_wxid - varchar(32) - 发送人wxid
        - t_wxid - varchar(32) - 接收人wxid
        - g_wxid - varchar(32) - 群聊wxid
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_file'

    def add_file(self, method, uri, body, biz_code=''):
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


