from datetime import datetime
from collections import defaultdict
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
            txt_str = ExportWechatInfo.format_msgs(msgs, users, g_wxid, db)
            File.save_file(txt_str, g_wxid_dir + date_dir + '/chat_list.txt', False)
        return True

    @staticmethod
    def format_msgs(msgs, users, g_wxid, db):
        sql = f'SELECT strNickName FROM Session WHERE strUsrName="{g_wxid}";'
        ret = db.execute(sql)
        room_name = ret[0][0] if ret else ''
        txt_str = f'微信群[{room_name}]聊天记录：\n'
        indent = '\t\t'
        # 创建用户映射字典
        user_map = {wxid: info['roomNickname'] if info['roomNickname'] else info['nickname'] for wxid, info in users.items()}
        for msg in msgs:
            msg['roomNickname'] = user_map.get(msg['talker'], '')
            msg['msg'] = str(msg['msg']).replace('\n', f'{indent}') \
                if msg['type_name'] in ['文本', '引用回复', '系统通知'] \
                else f'[{msg['type_name']}]'
        msgs = ExportWechatInfo.group_messages_by_time(msgs)
        for m_time in msgs:
            txt_str += f'\n{indent}{indent}[系统消息] {m_time}\n\n'
            for m in msgs[m_time]:
                txt_str += f'{indent}{m['roomNickname']} :  {m['msg']}\n'
        return txt_str

    @staticmethod
    def group_messages_by_time(msgs, interval_minutes=10):
        """
        按自定义时间间隔分组消息，使用组内第一个实际时间作为键名
        :param msgs: 消息列表
        :param interval_minutes: 分组时间间隔（分钟），默认10
        :return: { "首个时间": [同组消息...], ... }
        """
        time_groups = defaultdict(list)
        time_keys = {}  # 存储每个时间段的第一个实际时间
        for msg in msgs:
            # 解析消息时间
            msg_time = datetime.strptime(msg["CreateTime"], "%Y-%m-%d %H:%M:%S")
            # 计算时间段的起始时间点
            total_minutes = msg_time.hour * 60 + msg_time.minute
            floored_minutes = (total_minutes // interval_minutes) * interval_minutes
            floored_time = msg_time.replace(
                hour=floored_minutes // 60,
                minute=floored_minutes % 60,
                second=0,
                microsecond=0
            )
            # 使用时间段起始时间作为分组键
            time_slot = floored_time
            # 如果是该时间段的第一个消息，记录实际时间作为键名
            if time_slot not in time_keys:
                time_keys[time_slot] = msg["CreateTime"]
            # 添加到对应分组
            time_groups[time_slot].append(msg)
        # 转换为最终格式：用首个实际时间作为键
        return {
            time_keys[time_slot]: group_msgs
            for time_slot, group_msgs in time_groups.items()
        }

    @staticmethod
    def daily_task(params):
        """
        每日任务自动化 - db -> list -> export -> txt -> ai -> md -> img
        :param params: 请求入参，主要包含微信相关参数，日期不传默认今日
        :return: 自动化每个步骤执行的结果
        """
        return True





