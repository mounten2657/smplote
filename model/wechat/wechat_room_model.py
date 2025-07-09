import random
from service.wechat.callback.vp_command_service import VpCommandService
from tool.db.mysql_base_model import MysqlBaseModel
from tool.db.cache.redis_client import RedisClient
from tool.core import Ins, Attr, Time, Config


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

    def check_room_info(self, room, info):
        """检查是否有变化"""
        if not room['g_wxid']:
            return 0
        pid = info['id']
        g_wxid = info['g_wxid']
        app_key = info['app_key']
        change_log = info['change_log'] if info['change_log'] else []
        # 比较两个信息，如果有变动，就插入变更日志
        fields = ['nickname', 'notice', 'member_count', 'owner', 'head_img_url', 'member_list']
        change = Attr.data_diff(Attr.select_keys(info, fields), Attr.select_keys(room, fields), 'wxid')
        if change:
            update_data = {}
            for k, v in change.items():
                update_data[k] = room[k]
            change['_dt'] = Time.date()
            change_log.append(change)
            if len(change_log) > 60:
                change_log.pop(0)
            update_data['change_log'] = change_log
            self.update({"id": pid}, update_data)
            self.check_member_change(change, g_wxid, app_key)
        return True

    def check_member_change(self, change, g_wxid, app_key):
        """检查群成员变化并发送通知"""
        change_str = change.get('member_list', '')
        if not change_str:
            return False
        changes = self.extract_member_change(change_str)
        commander = VpCommandService(app_key, g_wxid)
        # 不是特定群不发消息
        config = Config.vp_config()
        app_config = config['app_list'][app_key]
        g_wxid_list = app_config['g_wxid']
        if g_wxid not in g_wxid_list:
            return False
        if changes.get('del'):  # 退群提醒
            del_list = changes.get('del')
            reason_list = ["群主没有发红包", "群主没有分配对象", "群主没有定期发放福利",
                           "没有滴到对象", "缺乏关爱", "生某人的气了", "一怒之下怒了一下",
                           "蹭不到图", "跑图被丢", "没有CP", "被冥龙创哭", "emo了", "想静静",
                           "没有吃到肯德基", "山高路远江湖再见，且行且珍惜！"
                           ]
            reason = random.choice(reason_list)
            for d in del_list:
                title = '【退群提醒】'
                des = f"成员：{d['display_name']} {Time.date('%H:%M')} 退群\r\n"
                des += f"原因：{reason}"
                self._del_user_cache(d['wxid'])
                commander.vp_card_msg(title, des)
            self._del_room_cache(g_wxid)
        if changes.get('add'):  # 入群提醒
            add_list = changes.get('add')
            for d in add_list:
                title = f"【欢迎新成员】"
                des = f"微信昵称：{d['display_name']}\r\n"
                des += f"入群日期：{Time.date()}"
                commander.vp_card_msg(title, des)
            self._del_room_cache(g_wxid)
        if changes.get('update'):  # 修改昵称提醒
            update_list = changes.get('update')
            for d in update_list:
                title = f"【马甲变更】"
                des = f"旧昵称：{d['before']['display_name']}\r\n"
                des += f"新昵称：{d['after']['display_name']}"
                d_wxid = Attr.get_by_point(d, 'before.wxid', Attr.get_by_point(d, 'after.wxid', ''))
                if d_wxid:
                    self._del_user_cache(d_wxid)
                commander.vp_card_msg(title, des)
        return True

    def _del_room_cache(self, g_wxid):
        """删除群聊缓存"""
        redis = RedisClient()
        redis.delete('VP_ROOM_INFO', [g_wxid])
        redis.delete('VP_ROOM_GRP_INF', [g_wxid])
        redis.delete('VP_ROOM_GRP_USL', [g_wxid])
        return True

    def _del_user_cache(self, wxid):
        """删除用户缓存"""
        redis = RedisClient()
        redis.delete('VP_USER_INFO', [wxid])
        redis.delete('VP_USER_FRD_INF', [wxid])
        return True

    @staticmethod
    def extract_member_change(change_str):
        """
        从字符串中匹配出群成员的变化
        output:
        {
            "del": [
                {"wxid": "wxid_121", "display_name": "昵称1"},
                {"wxid": "wxid_124", "display_name": "昵称4"},
                {"wxid": "wxid_125", "display_name": "昵称5"}
            ],
            "add": [
                {"wxid": "wxid_122", "display_name": "昵称2"}
            ],
            "update": [
                {
                    "before": {"wxid": "wxid_123", "display_name": "昵称3"},
                    "after": {"wxid": "wxid_123", "display_name": "昵称31"}
                }
            ]
        }
        """
        result = {
            "del": [],
            "add": [],
            "update": []
        }
        if not change_str:
            return result
        # 分割每条记录
        records = change_str.split('||')
        for record in records:
            if not record:
                continue
            # 分割索引和内容部分
            parts = record.split(':', 1)
            if len(parts) < 2:
                continue
            # 解析字段定义和值
            fields_part = parts[0]  # 如 "17.wxid;display_name"
            values_part = parts[1]  # 如 "wxid1;name1-->wxid2;name2" 或 "wxid1;name1-->"
            # 提取字段名
            fields = fields_part.split('.', 1)[1].split(';')  # ["wxid", "display_name"]
            # 分割前后值
            if '-->' in values_part:
                before, after = values_part.split('-->', 1)
            else:
                before, after = values_part, ''
            # 情况1: 退群 (有before无after)
            if before and not after:
                values = before.split(';')
                if len(values) == len(fields):
                    member = dict(zip(fields, values))
                    result["del"].append(member)
            # 情况2: 入群 (无before有after)
            elif not before and after:
                values = after.split(';')
                if len(values) == len(fields):
                    member = dict(zip(fields, values))
                    result["add"].append(member)
            # 情况3: 修改 (前后都有值)
            elif before and after:
                before_values = before.split(';')
                after_values = after.split(';')
                if len(before_values) == len(fields) and len(after_values) == len(fields):
                    before_dict = dict(zip(fields, before_values))
                    after_dict = dict(zip(fields, after_values))
                    # 检查是否有实际变化
                    if before_dict != after_dict:
                        result["update"].append({
                            "before": before_dict,
                            "after": after_dict
                        })
        return result

    def get_room_info(self, g_wxid):
        """获取群聊信息"""
        return self.where({"g_wxid": g_wxid}).first()
