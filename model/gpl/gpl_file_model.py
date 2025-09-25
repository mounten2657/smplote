from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class GplFileModel(MysqlBaseModel):
    """
    股票文件表
        - id - bigint - 主键ID
        - symbol - varchar(16) - 股票代码(带市场前缀)
        - symbol_name - varchar(64) - 股票名称
        - season_date - date - 季度尾日
        - biz_code - varchar(16) - 业务代码
        - url - varchar(2048) - 文件链接
        - fake_path - varchar(2048) - 虚拟路径
        - save_path - varchar(512) - 真实路径
        - file_name - varchar(255) - 文件名
        - file_size - int - 文件大小(byte)
        - file_md5 - varchar(32) - 文件md5
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_file'

    def add_gpl_file(self, file):
        """数据入库"""
        insert_data = {
            "symbol": file['symbol'],
            "symbol_name": file['symbol_name'],
            "season_date": file['season_date'],
            "biz_code": file['biz_code'],
            "url": file['url'],
            "fake_path": file['fake_path'],
            "save_path": file['save_path'],
            "file_name": file['file_name'],
            "file_size": file['size'],
            "file_md5": file['md5'],
        }
        return self.insert(insert_data)

    def get_gpl_file(self, md5):
        """获取文件信息"""
        return self.where({"file_md5": md5}).first()

    def get_gpl_file_list(self, biz_code, symbol, season_date):
        """获取业务文件列表"""
        where = {"biz_code": biz_code}
        db = self.where(where)
        if symbol:
            db = db.where({"symbol": symbol})
            db = db.order('season_date', 'desc')
        if season_date:
            db = db.where({"season_date": season_date})
        return db.get()
