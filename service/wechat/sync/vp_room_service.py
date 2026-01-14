from service.wechat.reply.vp_msg_service import VpMsgService
from service.wechat.sync.vp_user_service import VpUserService
from model.wechat.wechat_room_model import WechatRoomModel
from model.wechat.wechat_user_model import WechatUserModel
from tool.db.cache.redis_client import RedisClient
from tool.core import Attr, Time, Config, Logger
from utils.wechat.vpwechat.vp_client import VpClient

logger = Logger()
redis = RedisClient()


class VpRoomService:

    def _del_room_cache(self, g_wxid):
        """删除群聊缓存"""
        redis.delete('VP_ROOM_INFO', [g_wxid])
        redis.delete('VP_ROOM_GRP_INF', [g_wxid])
        redis.delete('VP_ROOM_GRP_USL', [g_wxid])
        return True

    def _del_user_cache(self, wxid):
        """删除用户缓存"""
        redis.delete('VP_USER_INFO', [wxid])
        redis.delete('VP_USER_FRD_INF', [wxid])
        return True

    def _get_user_head(self, g_wxid, u_wxid, app_key):
        """
        获取群用户头像 - 优先从缓存中获取

        :param g_wxid:  群wxid
        :param u_wxid:  用户wxid
        :return: 用户头像
        """
        client = VpClient(app_key)
        user = client.get_room(g_wxid, u_wxid)
        if not user:
            return ''
        head = user.get('small_head_img_url', '')
        # 如果缓存中没有，再从数据库中取
        if not head:
            user = WechatUserModel().get_user_info(u_wxid)
            head = user.get('head_img_url', '')
        return head

    def check_room_info(self, room, info, is_force=0):
        """检查是否有变化 - 由定时任务触发"""
        res = {}
        if not room['g_wxid'] or not room['nickname']:
            return 0
        rdb = WechatRoomModel()
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
            m_len = len(Attr.get(update_data, 'member_list', []))
            if not m_len and not update_data.get('head_img_url'):
                logger.error(f"获取群成员失败 - {pid} - {update_data} - {change}", 'ROOM_EMP_MEM')
                return 0
            update_data['change_log'] = change_log
            res['u'] = rdb.update({"id": pid}, update_data)
            res['c'] = self.check_member_change(change, g_wxid, app_key, is_force)
        # 后续操作
        res['m'] = self.update_member_info(g_wxid, room, app_key)  # 有则更新，无则新增
        res['r'] = redis.set('VP_ROOM_GRP_RMK', info['remark'], [g_wxid])  # 更新一下群备注
        return res

    def check_member_change(self, change, g_wxid, app_key, is_force=0):
        """检查群成员变化并发送通知"""
        change_str = change.get('member_list', '')
        if not change_str:
            return False
        changes = self.extract_member_change(change_str)
        # 不是特定群不发消息
        config = Config.vp_config()
        app_config = config['app_list'][app_key]
        g_wxid_list = app_config['g_wxid']
        self_wxid = app_config['wxid']
        if g_wxid not in g_wxid_list:
            return False
        if changes.get('del'):  # 退群提醒
            del_list = changes.get('del')
            if len(del_list) <= 3 and not is_force:
                for d in del_list:
                    c_head = self._get_user_head(g_wxid, d['wxid'], app_key)
                    VpMsgService.vp_quit_room(d['display_name'], c_head, g_wxid, app_key)
                    self._del_user_cache(d['wxid'])
            self._del_room_cache(g_wxid)
        if changes.get('add'):  # 入群提醒
            # 在格式化消息时已经发送，这里就不重新发送了
            self._del_room_cache(g_wxid)
        if changes.get('update'):  # 修改昵称提醒
            update_list = changes.get('update')
            for d in update_list:
                d_wxid = Attr.get_by_point(d, 'before.wxid', Attr.get_by_point(d, 'after.wxid', ''))
                if d_wxid and not is_force:
                    if d_wxid != self_wxid:
                        c_head = self._get_user_head(g_wxid, d['wxid'], app_key)
                        VpMsgService.vp_change_name(d['before']['display_name'], d['after']['display_name'], c_head, g_wxid, app_key)
                    self._del_user_cache(d_wxid)
        return True

    def update_member_info(self, g_wxid, room, app_key):
        """
        更新群里用户信息
          - 每次更新相隔两小时
          - 因为消息同步时，只能同步已发言的成员，如果该成员一直没有发言，则不会同步，故需要定时任务同步
          - 而且消息同步时的成员同步，其作用基本等同于初始化
        """
        res = {}
        member_list = room.get('member_list', [])
        if not member_list:
            return False
        if not redis.set_nx('VP_ROOM_USR_UP_LOCK', 1, [g_wxid]):  # 更新限速
            return False
        client = VpClient(app_key)
        udb = WechatUserModel()
        vus = VpUserService()
        # 依次检查并插入用户
        for member in member_list:    # [{"wxid":"wxid_xxx","display_name":"xxx"}]
            wxid = member.get('wxid')
            if not wxid:
                continue
            u_info = udb.get_user_info(wxid)
            if u_info:  # 已经入库了，就只检查一下用户头像
                if not redis.set_nx('VP_ROOM_USR_IMG_LOCK', 1, [wxid]):  # 更新限速
                    continue
                vus.check_img_info(u_info, u_info['head_img_url'], u_info['sns_img_url'])
                continue
            user = client.get_user(wxid, g_wxid)
            if not user.get('wxid'):
                continue
            res[wxid] = {}
            user['room_list'] = {g_wxid: room['nickname']} if room else {}
            user['is_friend'] = client.get_user_is_friend(wxid)
            user['user_type'] = 1 if user['is_friend'] else 2
            user['wx_nickname'] = user['nickname']
            res[wxid] = udb.add_user(user, app_key)
        return res

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



