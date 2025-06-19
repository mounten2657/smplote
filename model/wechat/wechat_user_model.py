from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins, Attr, Time, Str
from service.vpp.vpp_serve_service import VppServeService
from model.wechat.wechat_file_model import WechatFileModel


@Ins.singleton
class WechatUserModel(MysqlBaseModel):
    """
    微信用户表
        - id - int - 主键ID
        - wxid - varchar(32) - 用户微信ID
        - p_wxid - varchar(32) - 自定义微信ID
        - user_type - tinyint(1) - 用户类型(1好友|2群聊)
        - wx_nickname - varchar(64) - 微信昵称
        - remark_name - varchar(64) - 备注名
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

    def check_user_info(self, user, info, g_wxid=''):
        """检查是否有变化"""
        if not user['wxid']:
            return 0
        pid = info['id']
        change_log = info['change_log'] if info['change_log'] else []
        # 比较两个信息，如果有变动，就插入变更日志
        fields = ['p_wxid', 'wx_nickname', 'remark_name', 'head_img_url', 'h_fid',
                  'sex', 'signature', 'country', 'province', 'sns_img_url', 'sns_privacy', 's_fid',
                  'description', 'phone_list', 'label_id_list', 'label_name_list', 'room_list']
        if not g_wxid:
            fields.append('user_type')
        change = Attr.data_diff(Attr.select_keys(info, fields), Attr.select_keys(user, fields), 'wxid')
        if change:
            update_data = {}
            for k, v in change.items():
                update_data[k] = user[k]
            change['_dt'] = Time.date()
            change_log.append(change)
            if len(change_log) > 30:
                change_log.pop(0)
            update_data['change_log'] = change_log
            self.update({"id": pid}, update_data)
            h_img = update_data.get('head_img_url')
            s_img = update_data.get('sns_img_url')
            if h_img or s_img:
                self.check_img_info(info, h_img, s_img)
        return True

    def check_img_info(self, info, h_img, s_img):
        """更新用户图片"""
        pid = info['id']
        wxid = info['wxid']
        client = VppServeService()
        update_data = {}
        if h_img:
            f_info = self._download_user_img(client, h_img, 'head', wxid)
            if f_info:
                update_data['h_fid'] = f_info['id']
        if s_img:
            f_info = self._download_user_img(client, s_img, 'sns', wxid)
            if f_info:
                update_data['s_fid'] = f_info['id']
        if update_data:
            self.update({"id": pid}, update_data)
        return update_data

    def _download_user_img(self, client, img_url, f_type, wxid):
        """下载用户图片"""
        f_info = {}
        fn = Str.md5(img_url) + '.png'
        fd = f"{f_type}/{Time.date('%Y%m')}/"
        file = client.download_website_file(img_url, 'VP_USER', fn, fd)
        if file.get('url'):
            fdb = WechatFileModel()
            f_info = fdb.get_file_info(file['md5'])
            if not f_info:
                fdb.add_file(file, {
                    "send_wxid": wxid,
                    "send_wxid_name": fn,
                    "pid": 0,
                    "msg_id": 0,
                    "to_wxid": '',
                    "to_wxid_name": '',
                    "g_wxid": Time.date('%Y%m%d'),
                    "g_wxid_name": f_type,
                })
                f_info = fdb.get_file_info(file['md5'])
        return f_info

    def get_user_info(self, wxid):
        """获取用户信息"""
        return self.where({"wxid": wxid}).first()

    def get_user_list(self, wxid_list, chunk_size=50):
        """获取用户列表（自动分块查询避免SQL语句过长）

        Args:
            wxid_list: 微信ID列表
            chunk_size: 每批查询的数量，默认为50

        Returns:
            查询结果列表
        """
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
