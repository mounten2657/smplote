from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatFileModel(MysqlBaseModel):
    """
    微信文件表
        - id - bigint - 主键ID
        - url - varchar(1024) - 文件链接
        - fake_path - varchar(1024) - 虚拟路径
        - save_path - varchar(512) - 真实路径
        - file_name - varchar(512) - 文件名
        - biz_code - varchar(32) - 业务代码
        - s_wxid - varchar(32) - 发送人wxid
        - s_wxid_name - varchar(64) - 发送人昵称
        - file_size - int - 文件大小(byte)
        - file_md5 - varchar(32) - 文件md5
        - pid - bigint - 队列ID
        - msg_id - bigint - 消息ID
        - t_wxid - varchar(32) - 接收人wxid
        - t_wxid_name - varchar(64) - 接收人昵称
        - g_wxid - varchar(32) - 群聊wxid
        - g_wxid_name - varchar(64) - 群聊昵称
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_file'

    def add_file(self, file, message):
        """数据入库"""
        insert_data = {
            "url": file['url'],
            "fake_path": file['fake_path'],
            "save_path": file['save_path'],
            "file_name": file['file_name'],
            "biz_code": file['biz_code'],
            "s_wxid": message['send_wxid'],
            "s_wxid_name": message['send_wxid_name'],
            "file_size": file['size'],
            "file_md5": file['md5'],
            "pid": message['pid'],
            "msg_id": message['msg_id'],
            "t_wxid": message['to_wxid'],
            "t_wxid_name": message['to_wxid_name'],
            "g_wxid": message['g_wxid'],
            "g_wxid_name": message['g_wxid_name'],
        }
        return self.insert(insert_data)

    def get_file_info(self, md5):
        """获取文件信息"""
        return self.where({"file_md5": md5}).first()

    def get_biz_file_info(self, biz_code, s_wxid, s_wxid_name):
        """获取业务文件信息"""
        return self.where({"biz_code": biz_code, "s_wxid": s_wxid, "s_wxid_name": s_wxid_name}).first()
