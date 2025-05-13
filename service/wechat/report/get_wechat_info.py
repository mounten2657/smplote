import os
from pywxdump import *
from tool.core import *


class GetWechatInfo:

    @staticmethod
    def get_real_time_wx_info(wxid: str = '', index: int = 0, save_path: str = ''):
        """
        根据wxid实时获取本地微信信息(account,mobile,nickname,mail,wxid,key)
        :param wxid:  wxid，自己查看本地微信文件夹获取
        :param index:  返回列表的第几个
        :param save_path:  保存路径，具体到文件
        :return: 返回微信信息 {"pid": pid, "version": version, "account": account,
                              "mobile": mobile, "nickname": nickname, "mail": mail, "wxid": wxid,
                              "key": key, "wx_dir": wx_dir}
        """
        try:
            save_path = save_path if save_path else f'{Config.sqlite_db_dir()}/wx_sys_info.json'
            wx_info = get_wx_info(is_print=False, save_path=save_path)
            File.deduplicate_json_file(save_path, 'wxid')
            if wxid:
                matching_item = next((item for item in wx_info if item['wxid'] == wxid), None)
            else:
                matching_item = wx_info[index]
            if matching_item:
                return matching_item
            else:
                return Api.error(f"未能从获取微信信息中找到数据库密钥")
        except Exception as e:
            return Api.error(f"获取本地微信密钥时出错: {e}")

    @staticmethod
    def get_local_wx_info(wxid: str):
        """
        根据wxid获取本地的微信账户配置信息
        :param wxid: wxid，自己查看本地微信文件夹获取
        :return: 返回微信信息 {"pid": pid, "version": version, "account": account,
                              "mobile": mobile, "nickname": nickname, "mail": mail, "wxid": wxid,
                              "key": key, "wx_dir": wx_dir}
        """
        wx_info = File.read_file(f'{Config.sqlite_db_dir()}/wx_sys_info.json')
        return Attr.select_item_by_where(wx_info, {'wxid': wxid})

    @staticmethod
    def decrypt_wx_core_db(wxid: str, params: dict,  save_path: str = ''):
        """
        解密合并数据库 msg.db, microMsg.db, media.db
        :param wxid: wxid，自己查看本地微信文件夹获取
        :param save_path: 数据库输出路径
        :param params: 请求入参，包含所有请求参数
        :return: (true,解密后的数据库路径) or (false,错误信息)
        """
        try:
            # 时间处理，以便更好理解
            start_time, end_time = Time.start_end_time_list(params)
            # 没有时间参数，默认拉取最近七天的数据
            if not start_time and not end_time:
                start_time, end_time = (Time.now() - 7 * 86400, Time.now())
            save_path = save_path if save_path else Config.sqlite_db_dir()
            merge_save_path = os.path.join(save_path, 'wx_core.db' if start_time > 10 else 'wx_all_pass.db')
            wx_info = GetWechatInfo.get_local_wx_info(wxid)
            code, merge_save_path = decrypt_merge(
                key=wx_info.get('key'),
                wx_path=wx_info.get('wx_dir'),
                outpath=save_path ,
                merge_save_path=merge_save_path,
                startCreateTime=start_time,
                endCreateTime=end_time
            )
            if code:
                return merge_save_path
            else:
                return Api.error(f"解密微信核心数据库失败: {merge_save_path}")
        except Exception as e:
            err = Error.handle_exception_info(e)
            return Api.error(f"解密微信核心数据库时出错: {e}", err)

    @staticmethod
    def merge_wx_real_time_db(wxid: str,  merge_path: str = ''):
        """
        合并实时数据库 msg.db, microMsg.db, media.db
        :param wxid: wxid，自己查看本地微信文件夹获取
        :param merge_path: 数据库输出路径
        :return: (true,解密后的数据库路径) or (false,错误信息)
        """
        try:
            merge_path = merge_path if merge_path else f'{Config.sqlite_db_dir()}/wx_real_time.db'
            wx_info = GetWechatInfo.get_local_wx_info(wxid)
            code, merge_path = all_merge_real_time_db(
                key=wx_info.get('key'),
                wx_path=wx_info.get('wx_dir'),
                merge_path=merge_path
            )
            if code:
                return merge_path
            else:
                return Api.error(f"合并微信实时数据库失败: {merge_path}")
        except Exception as e:
            return Api.error(f"合并微信实时数据库时出错: {e}")

    @staticmethod
    def get_user_list(wxid: str, wxid_dir: str):
        """
        获取并保存用户列表
        :param wxid: wxid，自己查看本地微信文件夹获取
        :param wxid_dir:  数据保存位置，来自 config/wx.json
        :return: 用户列表 {"wxid_123456":{"wxid":"xxx","nickname":"xxx", ...}, ...}
        """
        db_config = Config.sqlite_db_config()
        db = DBHandler(db_config, wxid)
        users = db.get_user()
        File.save_file(users, wxid_dir + '/users.json', False)
        return users[wxid]

    @staticmethod
    def get_chat_list(wxid: str, wxid_dir: str):
        """
        获取并保存聊天列表
        :param wxid: wxid，自己查看本地微信文件夹获取
        :param wxid_dir:  数据保存位置，来自 config/wx.json
        :return: 聊天列表 [{"id":100,"MsgSvrId":"xxx","type_name":"文本", ...},{...}]
        """
        db_config = Config.sqlite_db_config()
        db = DBHandler(db_config, wxid)
        msgs, users = db.get_msgs()
        File.save_file(msgs, wxid_dir + '/charts.json', False)
        return msgs[0]

    @staticmethod
    def get_session_list(wxid: str, wxid_dir: str):
        """
        获取并保存用户列表
        :param wxid: wxid，自己查看本地微信文件夹获取
        :param wxid_dir:  数据保存位置，来自 config/wx.json
        :return: 会话列表
        """
        db_config = Config.sqlite_db_config()
        db = DBHandler(db_config, wxid)
        result = db.get_session_list()
        File.save_file(result, wxid_dir + '/sessions.json', False)
        return next(iter(result.values()))

    @staticmethod
    def get_room_list(wxid: str, wxid_dir: str):
        """
        获取并保存用户列表
        :param wxid: wxid，自己查看本地微信文件夹获取
        :param wxid_dir:  数据保存位置，来自 config/wx.json
        :return: 群聊列表
        """
        db_config = Config.sqlite_db_config()
        db = DBHandler(db_config, wxid)
        result = db.get_room_list()
        File.save_file(result, wxid_dir + '/rooms.json', False)
        return next(iter(result.values()))





