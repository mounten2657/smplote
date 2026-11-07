from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class BizFileModel(MysqlBaseModel):
    """
    业务文件表
        - id - bigint - 主键ID
        - url - varchar(1024) - 文件链接
        - fake_path - varchar(1024) - 虚拟路径
        - save_path - varchar(512) - 真实路径
        - file_name - varchar(512) - 文件名
        - biz_code - varchar(32) - 业务代码
        - sub_type - varchar(32) - 子类别
        - file_size - int - 文件大小(byte)
        - file_md5 - varchar(32) - 文件md5
        - origin_url - varchar(1024) - 文件源地址
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'biz_file'

    def add_file(self, file, data):
        """数据入库"""
        insert_data = {
            "url": file['url'],
            "fake_path": file['fake_path'],
            "save_path": file['save_path'],
            "file_name": file['file_name'],
            "biz_code": data['biz_code'],
            "sub_type": data['sub_type'],
            "file_size": file['size'],
            "file_md5": file['md5'],
            "origin_url": data['origin_url'],
        }
        return self.insert(insert_data)

    def get_file_info(self, md5):
        """获取文件信息"""
        return self.where({"file_md5": md5}).first()

    def get_biz_file_info(self, biz_code, sub_type, file_name):
        """获取业务文件信息"""
        return self.where({"biz_code": biz_code, "sub_type": sub_type, "file_name": file_name}).first()
