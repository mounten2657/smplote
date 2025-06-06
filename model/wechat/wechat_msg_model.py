from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatMsgModel(MysqlBaseModel):
    """
    微信用户标签表
        - id - int - 主键ID
        - msg_id - bigint - 消息ID
        - content - longtext - 消息内容
        - content_type - varchar(8) - 识别消息类型
        - msg_time - datetime - 消息时间
        - s_wxid - varchar(32) - 发送方wxid
        - s_wxid_name - varchar(64) - 发送方名称
        - is_my - tinyint(1) - 是否自己的消息(0否1是)
        - is_at - tinyint(1) - 是否艾特自己(0否1是)
        - is_sl - tinyint(1) - 是否私聊(0否1是)
        - is_group - tinyint(1) - 是否群聊(0否1是)
        - msg_type - int - 微信消息类型
        - app_key - varchar(4) - 应用账户：a1|a2
        - g_wxid - varchar(32) - 群聊ID(非群聊为0)
        - g_wxid_name - varchar(64) - 群聊名称
        - t_wxid - varchar(32) - 接收方wxid
        - t_wxid_name - varchar(64) - 接收方名称
        - f_wxid - varchar(32) - 来自方wxid
        - f_wxid_name - varchar(64) - 来自方名称
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

    def add_msg(self, msg, app_key, pid=0):
        """数据入库"""
        insert_data = {
            "msg_id": msg['msg_id'],
            "content": msg['content'],
            "content_type": msg['content_type'],
            "msg_time": msg['msg_time'],
            "s_wxid": msg['send_wxid'],
            "s_wxid_name": msg['send_wxid_name'] if msg['send_wxid_name'] else msg['send_wxid'],
            "is_my": msg['is_my'],
            "is_at": msg['is_at'],
            "is_sl": msg['is_sl'],
            "is_group": msg['is_group'],
            "msg_type": msg['msg_type'],
            "app_key": app_key,
            "g_wxid": msg['g_wxid'],
            "g_wxid_name": msg['g_wxid_name'],
            "t_wxid": msg['to_wxid'],
            "t_wxid_name": msg['to_wxid_name'] if msg['to_wxid_name'] else msg['to_wxid'],
            "f_wxid": msg['from_wxid'],
            "f_wxid_name": msg['from_wxid_name'] if msg['from_wxid_name'] else msg['from_wxid'],
            "at_user": msg['at_user'],
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
