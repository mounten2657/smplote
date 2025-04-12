from pywxdump import *
from tool.core import *


class ExportWechatInfo:

    @staticmethod
    def export_users(g_wxid: str, db_config: dict, g_wxid_dir: str):
        """
        导出某个群聊的群成员信息
        :param g_wxid: 群 wxid
        :param db_config:  数据库配置，来自 config/db.json
        :param g_wxid_dir:  数据保存位置，来自 config/wx.json
        :return: 群成员列表
        """
        db = DBHandler(db_config, g_wxid)
        result = db.get_room_list(roomwxids=[g_wxid])
        File.save_file(result, g_wxid_dir + '/user_list.json', False)
        return next(iter(result.values()))

    @staticmethod
    def export_chats(g_wxid: str, db_config: dict, g_wxid_dir: str, params: dict = None):
        """
        导出某个群聊的群成员信息
        :param g_wxid: 群 wxid
        :param db_config:  数据库配置，来自 config/db.json
        :param g_wxid_dir:  数据保存位置，来自 config/wx.json
        :param params:  请求入参，如页码和起止时间等参数
        :return: 群成员列表
        """
        if int(params.get('is_init', '0')) != 1 and not params.get('end_date'):
            params['end_date'] = Time.date("%Y-%m-%d")  # 默认导出今天的数据
        # 时间处理，以便更好理解
        start_time, end_time = Time.start_end_time_list(params)
        date_dir = Time.dft(end_time, "/%Y%m%d") if end_time else ''
        db = DBHandler(db_config, g_wxid)
        msgs, users = db.get_msgs(
            wxids=[g_wxid],
            start_index=params.get('start_index', 0),
            page_size=params.get('page_size', 99999),
            start_createtime=start_time,
            end_createtime=end_time
        )
        if not msgs:
            return Api.error('没有聊天记录')
        File.save_file(msgs, g_wxid_dir + date_dir + '/chat_list.json', False)
        if date_dir:
            # 有日期，说明是日报，继续生成 txt 文件
            users = File.read_file(g_wxid_dir + '/user_list.json')
            users = users.get(g_wxid, {}).get('wxid2userinfo', [])
            txt_str = ExportWechatInfo.format_msgs(msgs, users)
            File.save_file(txt_str, g_wxid_dir + date_dir + '/chat_list.txt', False)
        return True

    @staticmethod
    def format_msgs(msgs, users):
        txt_str = '\n'
        # 创建用户映射字典
        user_map = {wxid: info['roomNickname'] if info['roomNickname'] else info['nickname'] for wxid, info in users.items()}
        for msg in msgs:
            msg['roomNickname'] = user_map.get(msg['talker'], '')
            msg['msg'] = str(msg['msg']).replace('\n\n', ' \n') if msg['type_name'] in ['文本', '引用回复'] else f'[{msg['type_name']}]'
            txt_str += f'{msg['CreateTime']} {msg['roomNickname']} \n {msg['msg']}\n\n'
        return txt_str




