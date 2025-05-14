from datetime import datetime
from collections import defaultdict
from pywxdump import *
from tool.core import *
from tool.unit.img.md_to_img import MdToImg
from service.ai.report.ai_report_gen_service import AIReportGenService
from service.wechat.report.get_wx_info_service import GetWxInfoService
from model.wechat.sqlite.wx_core_model import WxCoreModel


class ExportWxInfoService:

    @staticmethod
    def export_users(g_wxid: str, g_wxid_dir: str):
        """
        导出某个群聊的群成员信息
        :param g_wxid: 群 wxid
        :param g_wxid_dir:  数据保存位置，来自 config/wx.json
        :return: 群成员列表
        """
        db_config = Config.sqlite_db_config()
        db = DBHandler(db_config, g_wxid)
        result = db.get_room_list(roomwxids=[g_wxid])
        date_dir = Time.dft(Time.now(), "/%Y%m%d")
        File.save_file(result, g_wxid_dir + date_dir + '/user_list.json', False)
        return True

    @staticmethod
    def export_chats(g_wxid: str, g_wxid_dir: str, params: dict = None):
        """
        导出某个群聊的群成员信息
        :param g_wxid: 群 wxid
        :param g_wxid_dir:  数据保存位置，来自 config/wx.json
        :param params:  请求入参，如页码和起止时间等参数
        :return: 群成员列表
        """
        if not params.get('end_date'):
            params['end_date'] = Time.date("%Y-%m-%d")  # 默认导出今天的数据
        # 时间处理，以便更好理解
        start_time, end_time = Time.start_end_time_list(params)
        date_dir = Time.dft(end_time, "/%Y%m%d")
        db_config = Config.sqlite_db_config()
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
        base_dir = g_wxid_dir + date_dir
        File.save_file(msgs, base_dir + '/chat_list.json', False)
        users = File.read_file(base_dir + '/user_list.json')
        users = users.get(g_wxid, {}).get('wxid2userinfo', [])
        txt_str = ExportWxInfoService.format_msgs(msgs, users, g_wxid)
        File.save_file(txt_str, base_dir + '/chat_list.txt', False)
        return True

    @staticmethod
    def format_msgs(msgs, users, g_wxid):
        db = WxCoreModel()
        room_name = db.get_room_name(g_wxid)
        # txt_str = f'微信群｢『 {room_name} 』｣聊天记录：\n'
        txt_str = f'微信群[{room_name}]聊天记录：\n'
        indent = '\t\t'
        # 创建用户映射字典
        user_map = {wxid: info['roomNickname'] if info['roomNickname'] else info['nickname'] for wxid, info in users.items()}
        for msg in msgs:
            msg['roomNickname'] = user_map.get(msg['talker'], '')
            msg['msg'] = str(msg['msg']).replace('\n', f'{indent}') \
                if msg['type_name'] in ['文本', '引用回复', '系统通知'] \
                else f'[{msg['type_name']}]'
        msgs = ExportWxInfoService.group_messages_by_time(msgs)
        for m_time in msgs:
            txt_str += f'\n{indent}{indent}[系统消息] {m_time}\n\n'
            for m in msgs[m_time]:
                txt_str += f'{indent}{m['roomNickname']} :  {m['msg']}\n'
        return txt_str

    @staticmethod
    def group_messages_by_time(msgs, interval_minutes=15):
        """
        按自定义时间间隔分组消息，使用组内第一个实际时间作为键名
        :param msgs: 消息列表
        :param interval_minutes: 分组时间间隔（分钟），默认15
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
    def daily_task(all_params):
        """
        每日任务自动化 - wx core db -> user & chat list -> json to txt -> ai -> md -> img
        :param all_params: 请求入参，主要包含微信相关参数，日期不传默认今日
        :return: 自动化每个步骤执行的结果
        """
        now_timestamp = Time.now()
        task_res = {"all_params": all_params}
        wxid, g_wxid, g_wxid_dir, params = map(all_params.get, ['wxid', 'g_wxid', 'g_wxid_dir', 'params'])
        re_db = int(params.get('re_db', '1'))  # 默认每次刷新数据库
        # 构建任务列表
        tasks = [
            ('wx_core_db', lambda: GetWxInfoService.decrypt_wx_core_db(wxid, params) if re_db else None),
            ('export_users', lambda: ExportWxInfoService.export_users(g_wxid, g_wxid_dir)),
            ('export_chats', lambda: ExportWxInfoService.export_chats(g_wxid, g_wxid_dir, params)),
            ('daily_report', lambda: AIReportGenService.daily_report(g_wxid_dir, params)),
            ('gen_img', lambda: MdToImg.gen_img(g_wxid_dir, params))
        ]
        # 执行任务
        for name, task in tasks:
            res = task()
            task_res[name] = res
            if Error.has_error(res):
                return task_res
        task_res['run_time'] = Time.now() - now_timestamp
        return task_res





