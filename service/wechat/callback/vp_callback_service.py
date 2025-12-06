from service.wechat.callback.vp_command_service import VpCommandService
from service.wechat.reply.vp_msg_service import VpMsgService
from service.wechat.sync.vp_room_service import VpRoomService
from service.wechat.sync.vp_user_service import VpUserService
from utils.wechat.vpwechat.vp_client import VpClient
from utils.wechat.vpwechat.callback.vp_callback_handler import VpCallbackHandler
from model.wechat.wechat_queue_model import WechatQueueModel
from model.wechat.wechat_file_model import WechatFileModel
from model.wechat.wechat_room_model import WechatRoomModel
from model.wechat.wechat_user_label_model import WechatUserLabelModel
from model.wechat.wechat_user_model import WechatUserModel
from model.wechat.wechat_msg_model import WechatMsgModel
from model.wechat.wechat_api_log_model import WechatApiLogModel
from tool.db.cache.redis_client import RedisClient
from tool.core import Logger, Time, Error, Attr, Config, Str, Sys

logger = Logger()
redis = RedisClient()


class VpCallbackService:

    @staticmethod
    def online_status(app_key):
        """获取在线状态"""
        res = VpClient(app_key).get_login_status()
        return res.get('Data') if res.get('Code') == 200 else False

    @staticmethod
    def start_ws(app_key):
        """启动 ws"""
        return VpClient(app_key).start_websocket()

    @staticmethod
    def close_ws(app_key):
        """关闭 ws"""
        return VpClient(app_key).close_websocket()

    @staticmethod
    def callback_handler_retry(app_key, params):
        """消息回放 - 多用于调试"""
        # vp_callback -> vp_callback_service -> vp_callback_handler -> vp_callback_service.callback_handler
        if params.get('ids'):  # 通过ID批量重试， 多个英文逗号隔开
            res = {}
            db = WechatQueueModel()
            id_list = str(params.get('ids')).split(',')
            queue_list = db.get_list_by_id(id_list)
            for queue in queue_list:
                queue['params'].update({
                    'is_retry': 1,
                    'is_force': params.get('is_force', 0),
                })
                res[queue['id']] = VpCallbackHandler(app_key).on_message(queue['params'])
                Time.sleep(0.1)
            return res
        else:  # 单个更新
            params.update({'is_retry': 1})
            return VpCallbackHandler(app_key).on_message(params)

    @staticmethod
    def refresh_room_info(app_key, g_wxid_str):
        """刷新群聊信息"""
        res = {}
        client = VpClient(app_key)
        rdb = WechatRoomModel()
        vrs = VpRoomService()
        config = Config.vp_config()
        app_config = config['app_list'][app_key]
        is_force = 1 if g_wxid_str else 0
        g_wxid_str = g_wxid_str if g_wxid_str else app_config['g_wxid']  # 只刷新已入驻的群聊
        g_list = str(g_wxid_str).split(',')
        for g_wxid in g_list:
            client.refresh_room(g_wxid)
            room = client.get_room(g_wxid)
            r_info = rdb.get_room_info(g_wxid)
            res[g_wxid] = vrs.check_room_info(room, r_info, is_force)
        return res

    @staticmethod
    def clear_api_log():
        """清理api日志"""
        return WechatApiLogModel().clear_history()

    def callback_handler(self, params):
        """推送事件预处理"""
        res = {}
        logger.debug(params['message'], 'VP_CALL_PAR')
        is_retry = params.get('is_retry', 0)  # 消息回放
        is_force = params.get('is_force', 0)  # 强制更新
        app_key = params.get('app_key')
        msg_id = params.get('message', {}).get('new_msg_id', 0)
        p_msg_id = params.get('message', {}).get('msg_id', 0)
        db = WechatQueueModel()
        info = db.get_by_msg_id(msg_id)
        if info:
            # msg_id 唯一 - 已入库且处理成功就跳过
            if not (is_force or (is_retry and not info['is_succeed'])):
                logger.warning(f"消息已入库 - 跳过 - [{p_msg_id}-{msg_id}]", 'VP_CALL_SKP')
                return 'success'
            res['insert_db'] = pid = info['id']
            logger.warning(f"消息重试 - {info['id']} - [{p_msg_id}-{msg_id}]", 'VP_CALL_RTY')
        else:
            # 数据入库
            res['insert_db'] = pid = db.add_queue(app_key, params, 'wechatpad')
            logger.debug(res, 'VP_CALL_IDB')
        # 更新处理数据
        update_data = {"process_params": {"params": "[PAR]", "app_key": app_key}}
        res['update_db'] = db.update_process(int(pid), update_data)
        # 实际处理逻辑
        res['que_sub'] = Sys.delayed_task(VpCallbackService.callback_handler_deal, pid, params)
        return 'success' if res['que_sub'] else 'error'

    @staticmethod
    def callback_handler_deal(pid, params):
        """微信回调真正处理逻辑"""
        res = {"pid": pid}
        db = WechatQueueModel()
        db.set_processed(pid)
        # 消息数据格式化
        res['rev_handler'], data = VpCallbackHandler.rev_handler(params)
        logger.debug(res['rev_handler'], 'VP_CALL_HD_RES')
        data['pid'] = pid
        # 消息数据入库 - 异步
        res['ins_handler'] = Sys.delayed_task(VpCallbackService.insert_handler, data)
        # 消息指令处理 - 异步
        res['cmd_handler'] = Sys.delayed_task(VpCallbackService.command_handler, data, timeout=300)
        update_data = {"process_result": res, "process_params": data}
        if res['rev_handler']:
            update_data.update({"is_succeed": 1})
        res['update_db'] = db.update_process(int(pid), update_data)
        return res

    @staticmethod
    def command_handler(data):
        """微信群消息指令处理入口"""
        try:
            app_key = data['app_key']
            is_at = data['is_at']
            s_wxid = data['send_wxid']
            g_wxid = data['g_wxid']
            content = data['content']
            msg_time = data['msg_time']
            if not content or not g_wxid:
                return False
            # 重试的命令不予处理
            if data.get('is_retry', 0):
                return False
            config = Config.vp_config()
            app_config = config['app_list'][app_key]
            # 拦截非允许群
            if g_wxid not in str(app_config['g_wxid']).split(','):
                return False
            # 超时的命令不予处理
            if Time.now() - Time.tfd(msg_time) > 900:
                return False
            commands = ",".join([config['command_list'], config['command_list_tj'], config['command_list_yl'], config['command_list_sky']]).split(',')
            content = Str.remove_at_user(content).strip()
            #先去掉#号再加上#号，这样不管带不带#号都能兼容
            n_list = ['提问', '点歌', '身高查询', '今日任务', '今日红石', '礼包查询', '光翼查询']  # 可省略 # 号的命令
            content = f"#{content.replace('#', '')}" if content.startswith(tuple(n_list)) else content
            if str(content).startswith(tuple(commands)):
                is_admin = s_wxid in str(config['admin_list']).split(',')
                commander = VpCommandService(app_key, g_wxid, s_wxid)
                content_str = str(content)
                def only_admin_str():
                    admin_str = "只有管理员才能使用该功能"
                    return VpMsgService.vp_normal_msg(admin_str, None, g_wxid, app_key)
                # 定义命令前缀与处理函数的映射关系
                command_map = {
                    # 数字命令
                    '1': {
                        '1': lambda: commander.vp_manual(content) if is_at else False,
                        '101': lambda: commander.vp_question(content),
                        '102': lambda: commander.vp_science(content),
                        '103': lambda: commander.vp_self(content) if is_at else False,
                    },
                    '2': {
                        '201': lambda: commander.vp_sky_rw(content),
                        '202': lambda: commander.vp_sky_hs(content),
                    },
                    # 特殊前缀命令（按优先级排序）
                    '#菜单': lambda: commander.vp_manual(content),            # [!] 加命令前别忘记在 config/vp.json 中也加上 !!!
                    '#提问': lambda: commander.vp_question(content),
                    '#百科': lambda: commander.vp_science(content),
                    '#新闻': lambda: commander.vp_xw(content),
                    '#任务': lambda: commander.vp_sky_rw(content),
                    '#今日任务': lambda: commander.vp_sky_rw(content),
                    '#红石': lambda: commander.vp_sky_hs(content),
                    '#今日红石': lambda: commander.vp_sky_hs(content),
                    '#公告': lambda: commander.vp_sky_gg(content),
                    '#日历': lambda: commander.vp_sky_rl(content),
                    '#先祖': lambda: commander.vp_sky_xz(content),
                    '#代币': lambda: commander.vp_sky_db(content),
                    '#季蜡': lambda: commander.vp_sky_jl(content),
                    '#大蜡': lambda: commander.vp_sky_dl(content),
                    '#魔法': lambda: commander.vp_sky_mf(content),
                    '#神龛': lambda: commander.vp_sky_permanent(content),
                    '#献祭': lambda: commander.vp_sky_permanent(content),
                    '#烛火': lambda: commander.vp_sky_permanent(content),
                    '#身高查询': lambda: commander.vp_sky_sg(content),
                    '#光翼查询': lambda: commander.vp_sky_gy(content),
                    '#礼包查询': lambda: commander.vp_sky_lb(content),
                    '#天气': lambda: commander.vp_zxz_tq(content),
                    '#v50': lambda: commander.vp_zxz_v50(content),
                    '#文案': lambda: commander.vp_ov_wa(content),
                    '#壁纸': lambda: commander.vp_ov_bz(content),
                    '#男友': lambda: commander.vp_bf(content),
                    '#女友': lambda: commander.vp_gf(content),
                    '#唱歌': lambda: commander.vp_ov_cg(content),
                    '#点歌': lambda: commander.vp_dg(content),
                    '#昨日榜': lambda: commander.vp_rank(content),
                    '#日榜': lambda: commander.vp_rank(content),
                    '#月榜': lambda: commander.vp_rank(content),
                    '#季榜': lambda: commander.vp_rank(content) if is_admin else False,
                    '#半年榜': lambda: commander.vp_rank(content) if is_admin else False,
                    '#年榜': lambda: commander.vp_rank(content) if is_admin else False,
                    '#设置': lambda: commander.vp_setting(content) if is_admin else only_admin_str(),
                    '#总结': lambda: commander.vp_report(content) if is_admin else False,
                }
                # 检查数字开头的命令
                if content_str and content_str[0] in ('1', '2'):
                    prefix_commands = command_map.get(content_str[0], {})
                    handler = prefix_commands.get(content_str, lambda: False)
                    return handler()
                # 检查特殊前缀命令
                for prefix, handler in command_map.items():
                    if isinstance(handler, dict):
                        continue  # 跳过已经处理过的数字前缀
                    if content_str.startswith(prefix):
                        return handler()
                # 非管理员拦截（所有管理命令都已在上面处理）
                if not is_admin:
                    return only_admin_str()
            # 默认返回
            return False
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"消息指令处理失败 - {data.get('content')} - {err}", "VP_CMD_ERR")
            return False

    @staticmethod
    def command_handler_retry(id_list):
        """微信消息指令处理重试"""
        return VpCallbackService._combine_handler_retry(id_list, 1)

    @staticmethod
    def insert_handler(data):
        """微信消息数据入库入口"""
        # 入库顺序： 群聊表 - 用户表 - 消息表
        pid = data['pid']
        qdb = WechatQueueModel()
        mdb = WechatMsgModel()
        cache_key = 'VP_MSG_INS_LOCK'
        try:
            res = {}
            app_key = data['app_key']
            msg_id = data.get('msg_id', 0)
            if not msg_id or not pid:
                logger.error(f"消息处理发生错误{[pid]} - {data}", 'VP_IHD_ERR')
                return False
            msg_type = data['content_type']
            g_wxid = data['g_wxid']
            s_wxid = data['send_wxid']
            t_wxid = data['to_wxid']
            self_wxid = data['self_wxid']
            config = Config.vp_config()
            app_config = config['app_list'][app_key]
            # 拦截非允许群
            if str(app_config['g_wxid_exc']) and str(app_config['g_wxid_exc']) in str(data):
                logger.warning(f"消息忽略 - 跳过 - [{msg_id}]", 'VP_INS_ING')
                return False
            # 还是得加锁，因为有重试机制，会导致消息重复推送
            Time.sleep(Str.randint(1, 10) / 10)
            if not redis.set_nx(cache_key, 1, [msg_id]):
                return False
            # 先判断消息有没有入库 - 已入库就不继续执行了
            m_info = mdb.get_msg_info(msg_id)
            is_retry = data.get('is_retry')
            if m_info and not is_retry:
                return True
            # 内容为空 - 直接跳过
            data['content'] = data.get('content', '')
            if not data['content']:
                return False
            # 只有一个消费者，所以不用加锁
            client = VpClient(app_key)
            res['upd_cnt_1'] = qdb.set_retry_count(pid, 1)
            user_list = [{"wxid": s_wxid}, {"wxid": t_wxid}]
            room = r_info = {}
            # 群聊入库
            if g_wxid:
                room = client.get_room(g_wxid)
                if not room.get('g_wxid'):
                    logger.warning(f"获取群聊信息失败 - 跳过 - [{g_wxid}]", 'VP_INS_ING')
                    return False
                rdb = WechatRoomModel()
                r_info = rdb.get_room_info(g_wxid)
                if not r_info:
                    res['ins_room'] = rdb.add_room(room, app_key)
                    r_info = rdb.get_room_info(g_wxid)
                user_list = room['member_list']
            # 标签更新
            ldb = WechatUserLabelModel()
            u_label = ldb.get_label(self_wxid)
            label = client.get_user_frd_lab()
            label = Attr.get_by_point(label, 'Data.labelPairList', [])
            if len(u_label) != len(label):
                res['ins_label'] = ldb.add_label(label, self_wxid)
            # 批量获取用户
            udb = WechatUserModel()
            wxid_list = [d["wxid"] for d in user_list]
            u_list = udb.get_user_list(wxid_list)

            # 用户入库耗时 - 改为异步执行
            if (g_wxid and r_info) or not g_wxid:
                t_data = {
                    "app_key": app_key,
                    "g_wxid": g_wxid,
                    "u_list": u_list,
                    "user_list": user_list,
                    "room": room
                }
                res['update_user'] = Sys.delayed_task(VpCallbackService.update_user, t_data, timeout=900)

            # 文件下载 - 由于消息是单次入库的，所以文件下载就不用重复判断了
            fid = 0
            data['g_wxid_name'] = room['nickname'] if room else ''
            if msg_type in ['gif', 'png', 'mp4', 'file', 'voice']:
                file = client.download_file(data)
                if file.get('url'):
                    fdb = WechatFileModel()
                    f_info = fdb.get_file_info(file['md5'])
                    if f_info:
                        fid = f_info['id']
                    else:
                        res['ins_file'] = fid = fdb.add_file(file, data)
            # 消息入库
            data['fid'] = fid
            if 'revoke' == msg_type:
                r_msg_id = data['content_link']['p_new_msg_id']
                r_msg = WechatQueueModel().get_by_msg_id(r_msg_id)
                if r_msg:
                    data['content'] += f"<{Attr.get_by_point(r_msg, 'process_params.content', '')}>"
            mid = m_info['id'] if m_info and m_info['id'] else 0
            up_key = 'upd_msg' if mid else 'ins_msg'
            res[up_key] = mdb.add_msg(data, app_key, mid)
            # 入库成功 - 更新队列表的 retry_count
            res['upd_cnt_2'] = qdb.set_retry_count(pid, 2)
            # 删除入库状态锁
            redis.delete(cache_key, [msg_id])
            return res
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"消息入库失败[{pid}] - {err}", "VP_INS_ERR")
            qdb.set_succeed(pid, 0)
            Sys.delayed_task(VpCallbackService.insert_handler_retry, [pid], delay_seconds=5)
            return False

    @staticmethod
    def update_user(data):
        """用户入库与更新"""
        res = {}
        app_key = data['app_key']
        g_wxid = data['g_wxid']
        u_list = data['u_list']
        user_list = data['user_list']
        room = data['room']
        client = VpClient(app_key)
        udb = WechatUserModel()
        vus = VpUserService()
        config = Config.vp_config()
        app_config = config['app_list'][app_key]
        if g_wxid:
            Time.sleep(Str.randint(1, 10) / 10)
            # 群聊更新限速 - 六小时检查更新一次 - 不能依赖这个进行全部的用户更新 - 此处基本等效于初始化
            if not redis.set_nx('VP_ROOM_USR_LOCK', 1, [g_wxid]):
                return False
        for u in user_list:
            wxid = u['wxid']
            if not wxid:
                continue
            u_info = Attr.select_item_by_where(u_list, {"wxid": wxid})
            if not u_info:
                user = client.get_user(wxid, g_wxid)
                if not user.get('wxid'):
                    logger.warning(f"获取用户信息失败 - 跳过 - [{wxid}]", 'VP_INS_ING')
                    continue
                user['room_list'] = {g_wxid: room['nickname']} if room else {}
                user['is_friend'] = client.get_user_is_friend(wxid)
                user['user_type'] = 1 if user['is_friend'] else 2
                user['wx_nickname'] = user['nickname']
                res['ins_user'] = udb.add_user(user, app_key)
                u_info = udb.get_user_info(wxid)
                vus.check_img_info(u_info, u_info['head_img_url'], u_info['sns_img_url'])
            if u_info and (Time.now() - Time.tfd(str(u_info['update_at'])) > 3600):
                # 特定群才更新
                if g_wxid and g_wxid not in str(app_config['g_wxid']).split(','):
                    continue
                user = client.get_user(wxid, g_wxid)
                if not user.get('wxid'):
                    logger.warning(f"获取用户信息失败 - 跳过 - [{wxid}]", 'VP_INS_ING')
                    continue
                user['room_list'] = {g_wxid: room['nickname']} if room else {}
                if g_wxid:
                    user['is_friend'] = client.get_user_is_friend(wxid)
                user['user_type'] = 1 if user['is_friend'] else 2
                user['room_list'].update(u_info['room_list'])
                res['chk_user'] = vus.check_user_info(user, u_info, g_wxid)
        return res

    @staticmethod
    def insert_handler_retry(id_list):
        """微信消息数据入库重试"""
        return VpCallbackService._combine_handler_retry(id_list, 2)

    @staticmethod
    def _combine_handler_retry(id_list, r_type):
        """组合消息重试 - 多用于调试"""
        res = {}
        db = WechatQueueModel()
        queue_list = db.get_list_by_id(id_list)
        for queue in queue_list:
            pid = queue['id']
            queue['process_params'].update({
                'pid': pid,
            })
            process = queue['process_params']
            process.update({"is_retry": 1})
            if 1 == r_type:
                res[pid] = VpCallbackService.command_handler(process)
            else:
                res[pid] = VpCallbackService.insert_handler(process)
            Time.sleep(0.1)
        return res
