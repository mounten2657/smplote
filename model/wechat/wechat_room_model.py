from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatRoomModel(MysqlBaseModel):
    """
    微信群聊表
        - id - int - 主键ID
        - g_wxid - varchar(64) - 群聊微信ID
        - nickname - varchar(128) - 群昵称
        - quan_pin - varchar(128) - 全拼
        - encry_name - varchar(512) - 加密昵称
        - notice - text - 群公告
        - member_count - int - 群人数
        - owner - varchar(64) - 群主wxid
        - head_img_url - varchar(512) - 小头像URL
        - member_list - longtext - 群成员列表
        - change_log - text - 变更日志（最近60条）
        - app_key - varchar(4) - 应用账户：a1|a2
        - remark - varchar(255) - 备注
        - extra - text - 关联属性
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_room'

    def add_room(self, room, app_key):
        """数据入库"""
        if not room['g_wxid']:
            return 0
        info = self.get_room_info(room['g_wxid'])
        if info:
            return info['id']
        insert_data = {
            "app_key": app_key,
            "g_wxid": room['g_wxid'],
            "nickname": room['nickname'],
            "quan_pin": room['quan_pin'],
            "encry_name": room['encry_name'],
            "notice": room['notice'],
            "member_count": room['member_count'],
            "owner": room['owner'],
            "head_img_url": room['head_img_url'],
            "member_list": room['member_list'],
            "change_log": [],
            "remark": "",
            "extra": {},
        }
        return self.insert(insert_data)

    def get_room_info(self, g_wxid):
        """获取群聊信息"""
        return self.where({"g_wxid": g_wxid}).first()
