from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatUserModel(MysqlBaseModel):
    """
    微信用户表
        - id - int - 主键ID
        - wxid - varchar(32) - 用户微信ID
        - p_wxid - varchar(32) - 自定义微信ID
        - user_type - tinyint(1) - 用户类型(1好友|2群聊)
        - wx_nickname - varchar(128) - 微信昵称
        - remark_name - varchar(128) - 备注名
        - head_img_url - varchar(255) - 头像地址
        - h_fid - bigint(20) - 头像文件id
        - quan_pin - varchar(64) - 昵称全拼
        - encry_name - varchar(512) - 加密昵称
        - sex - tinyint(1) - 性别(0未知1男2女)
        - signature - varchar(255) - 个性签名
        - country - varchar(32) - 国家
        - province - varchar(32) - 城市
        - sns_img_url - varchar(512) - 朋友圈背景
        - s_fid - bigint(20) - 背景文件id
        - sns_privacy - bigint - 朋友圈时效
        - description - varchar(255) - 填写的备注
        - phone_list - varchar(255) - 填写的电话列表
        - label_id_list - varchar(255) - 标签ID列表
        - label_name_list - varchar(255) - 标签名列表
        - room_list - text - 关联的群聊列表
        - change_log - text - 变更日志（最近30条）
        - app_key - varchar(4) - 应用账户：a1|a2
        - remark - varchar(255) - 备注
        - extra - text - 关联属性
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_user'

    def add_user(self, user, app_key):
        """数据入库"""
        if not user['wxid']:
            return 0
        info = self.get_user_info(user['wxid'])
        if info:
            return info['id']
        insert_data = {
            "app_key": app_key,
            "wxid": user['wxid'],
            "p_wxid": user['p_wxid'],
            "user_type": user['user_type'],
            "wx_nickname": user['wx_nickname'],
            "remark_name": user['remark_name'],
            "head_img_url": user['head_img_url'],
            "h_fid": user.get('h_fid', 0),
            "quan_pin": user['quan_pin'],
            "encry_name": user['encry_name'],
            "sex": user['sex'],
            "signature": user['signature'],
            "country": user['country'],
            "province": user['province'],
            "sns_img_url": user['sns_img_url'],
            "s_fid": user.get('s_fid', 0),
            "sns_privacy": user['sns_privacy'],
            "description": user['description'],
            "phone_list": user['phone_list'],
            "label_id_list": user['label_id_list'],
            "label_name_list": user['label_name_list'],
            "room_list": user['room_list'],
            "change_log": [],
            "remark": "",
            "extra": {},
        }
        return self.insert(insert_data)

    def get_user_info(self, wxid):
        """获取用户信息"""
        return self.where({"wxid": wxid}).first()

    def get_user_list(self, wxid_list, chunk_size=50):
        """获取用户列表（自动分块查询避免SQL语句过长）"""
        if not wxid_list:
            return []
        # 对列表进行分块
        chunks = [wxid_list[i:i + chunk_size]
                  for i in range(0, len(wxid_list), chunk_size)]
        result = []
        for chunk in chunks:
            # 查询当前分块的数据
            chunk_result = self.where_in("wxid", chunk).get()
            if chunk_result:
                result.extend(chunk_result)
        return result
