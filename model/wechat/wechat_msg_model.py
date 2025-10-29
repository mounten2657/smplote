from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Time


@Ins.singleton
class WechatMsgModel(MysqlBaseModel):
    """
    微信用户标签表
        - id - int - 主键ID
        - msg_id - bigint - 消息ID
        - content - longtext - 消息内容
        - content_type - varchar(16) - 识别消息类型
        - msg_time - datetime - 消息时间
        - s_wxid - varchar(32) - 发送方wxid
        - s_wxid_name - varchar(128) - 发送方名称
        - is_my - tinyint(1) - 是否自己的消息(0否1是)
        - is_at - tinyint(1) - 是否艾特自己(0否1是)
        - is_sl - tinyint(1) - 是否私聊(0否1是)
        - is_group - tinyint(1) - 是否群聊(0否1是)
        - msg_type - int - 微信消息类型
        - app_key - varchar(4) - 应用账户：a1|a2
        - g_wxid - varchar(32) - 群聊ID(非群聊为0)
        - g_wxid_name - varchar(128) - 群聊名称
        - t_wxid - varchar(32) - 接收方wxid
        - t_wxid_name - varchar(128) - 接收方名称
        - f_wxid - varchar(32) - 来自方wxid
        - f_wxid_name - varchar(128) - 来自方名称
        - at_user - text - 艾特的用户列表
        - p_msg_id - bigint - 原始消息id
        - fid - bigint - 文件id
        - pid - bigint - 队列id
        - aid - bigint - AI聊天记录ID
        - lid - bigint - 微信接口日志ID
        - content_link - text - 内容属性
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_msg'

    def add_msg(self, msg, app_key, pid = 0):
        """数据入库"""
        insert_data = {
            "msg_id": msg['msg_id'],
            "content": msg['content'],
            "content_type": msg['content_type'],
            "msg_time": msg['msg_time'],
            "s_wxid": msg['send_wxid'],
            "s_wxid_name": msg['send_wxid_name'] if msg['send_wxid_name'] else msg['send_wxid'],
            "is_my": msg['is_my'],
            "is_at": 1 if msg['at_user'] else 0,
            "is_sl": msg['is_sl'],
            "is_group": 1 if msg['g_wxid'] else 0,
            "msg_type": msg['msg_type'],
            "app_key": app_key,
            "g_wxid": msg['g_wxid'],
            "g_wxid_name": msg['g_wxid_name'],
            "t_wxid": msg['to_wxid'],
            "t_wxid_name": msg['to_wxid_name'] if msg['to_wxid_name'] else msg['to_wxid'],
            "f_wxid": msg['from_wxid'],
            "f_wxid_name": msg['from_wxid_name'] if msg['from_wxid_name'] else msg['from_wxid'],
            "at_user": msg['at_user'] if msg['at_user'] else '',
            "p_msg_id": msg['p_msg_id'],
            "fid": msg['fid'],
            "pid": msg['pid'],
            "aid": int(msg.get('aid', 0)),
            "lid": int(msg.get('lid', 0)),
            "content_link": msg['content_link'],
        }
        if pid:  # 强制覆盖
            return self.update({"id": pid}, insert_data)
        return self.insert(insert_data)

    def get_msg_info(self, mid):
        """获取消息信息"""
        return self.where({"msg_id": mid}).first()

    def get_msg_list(self, g_wxid, m_date = ''):
        """获取消息列表 - 今日的最近1000条"""
        m_date = m_date if m_date else Time.dft(Time.now(), "%Y-%m-%d 00:00:00")  # 默认统计今日数据
        m_e_date = Time.dft(Time.tfd(m_date), "%Y-%m-%d 23:59:59")
        m_where = {"g_wxid": g_wxid, "msg_time": {"opt": "between", "val": [m_date, m_e_date]}}
        m_count = self.get_count(m_where)
        if m_count < 200:  # 数据小于200条，直接返回空
            return []
        return (((self.where(m_where)
                  .order('msg_time', 'desc'))
                  .limit(0, 1000))
                  .get())

    def get_msg_times_rank(self, g_wxid, m_date_list = None, limit = 5):
        """获取聊天记录前五名发言次数统计"""
        if m_date_list is None:
            m_date_list = ['', '']
        if not m_date_list[0]:  # 默认统计昨日数据
            m_date_list[0] = Time.dft(Time.now() - 86400, "%Y-%m-%d 00:00:00")
            m_date_list[1] = Time.dft(Time.tfd(m_date_list[0]), "%Y-%m-%d 23:59:59")
        m_date, m_e_date = m_date_list
        m_where = {"g_wxid": g_wxid, "msg_time": {"opt": "between", "val": [m_date, m_e_date]}}
        m_field = ['id', 'count(1) as count', 'g_wxid', 'g_wxid_name', 's_wxid', 's_wxid_name', 'msg_time']
        m_rank = (self.select(m_field)
                   .where(m_where)
                   .group('s_wxid')
                   .order('count', 'desc')
                   .limit(0, limit)
                   .get())
        if m_rank:
            return m_rank
        return []
