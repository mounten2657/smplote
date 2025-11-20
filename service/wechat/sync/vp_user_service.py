from service.vpp.vpp_serve_service import VppServeService
from model.wechat.wechat_user_model import WechatUserModel
from model.wechat.wechat_file_model import WechatFileModel
from tool.core import Attr, Time, Str


class VpUserService:

    def check_user_info(self, user, info, g_wxid=''):
        """检查是否有变化"""
        if not user['wxid']:
            return 0
        udb = WechatUserModel()
        pid = info['id']
        change_log = info['change_log'] if info['change_log'] else []
        # 比较两个信息，如果有变动，就插入变更日志
        fields = ['p_wxid', 'wx_nickname', 'remark_name', 'head_img_url',
                  'sex', 'signature', 'country', 'province', 'sns_img_url', 'sns_privacy',
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
            udb.update({"id": pid}, update_data)
            h_img = update_data.get('head_img_url')
            s_img = update_data.get('sns_img_url')
            if h_img or s_img:
                self.check_img_info(info, h_img, s_img)
        return True

    def check_img_info(self, info, h_img, s_img):
        """更新用户图片"""
        udb = WechatUserModel()
        pid = info['id']
        wxid = info['wxid']
        client = VppServeService()
        update_data = {}
        change = {}
        if h_img:
            f_info = self._download_user_img(client, h_img, 'head', wxid)
            if f_info:
                update_data['h_fid'] = f_info['id']
                if f_info['id'] != info['h_fid']:
                    change['h_fid'] = f"{info['h_fid']}-->{f_info['id']}"
        if s_img:
            f_info = self._download_user_img(client, s_img, 'sns', wxid)
            if f_info:
                update_data['s_fid'] = f_info['id']
                if f_info['id'] != info['s_fid']:
                    change['s_fid'] = f"{info['s_fid']}-->{f_info['id']}"
        if update_data:
            if change:
                change_log = info['change_log']
                change['_dt'] = Time.date()
                change_log.append(change)
                update_data['change_log'] = change_log
            udb.update({"id": pid}, update_data)
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
