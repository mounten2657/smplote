from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr


@Ins.singleton
class GplApiLogModel(MysqlBaseModel):
    """
    股票接口日志表
        - id - bigint - 主键ID
        - url - varchar(128) - 请求地址
        - biz_code - varchar(16) - 业务码
        - h_event - varchar(16) - 自定义字段，多为股票代码
        - h_value - varchar(24) - 自定义字段，多为时间日期
        - request_params - longtext - 请求参数
        - process_params - longtext - 处理参数
        - response_result - longtext - 返回结果
        - is_succeed - tinyint(1) - 是否成功(0否1是)
        - response_time - int - 响应耗时(ms)
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'gpl_api_log'

    def add_gpl_api_log(self, url, body, biz_code, ext):
        """股票日志数据入库"""
        body = body if body else {}
        he = Attr.get(ext, 'he', '')
        hv = Attr.get(ext, 'hv', '')
        # 先检查是否已经入库
        info = self.get_gpl_api_log(biz_code, he, hv)
        if info:
            return info
        insert_data = {
            "url": url,
            "biz_code": biz_code,
            "h_event": he,
            "h_value": hv,
            "request_params": body,
            "process_params": {},
            "response_result": {},
            "is_succeed": 0,
            "response_time": 0,
        }
        return self.insert(insert_data)

    def update_gpl_api_log(self, pid, data):
        """更新股票日志数据"""
        if not pid:
            return 0
        return self.update({'id': pid}, data)

    def get_gpl_api_log_list(self, biz_code, symbol_list, td_list):
        """获取股票日志列表"""
        return (self.where({'biz_code': biz_code, 'is_succeed': 1})
                .where_in('h_event', symbol_list)
                .where_in('h_value', td_list)
                .get())

    def get_gpl_api_log(self, biz_code, symbol, td):
        """获取单个股票日志数据"""
        return self.where({'biz_code': biz_code, 'h_event': symbol, 'h_value': td}).first()

