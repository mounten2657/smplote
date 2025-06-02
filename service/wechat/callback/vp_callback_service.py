from service.ai.command.ai_command_service import AiCommandService
from service.wechat.reply.send_wx_msg_service import SendWxMsgService
from service.wechat.sky.sky_data_service import SkyDataService
from tool.db.cache.redis_client import RedisClient
from utils.wechat.vpwechat.vp_client import VpClient
from utils.wechat.vpwechat.callback.vp_callback_handler import VpCallbackHandler
from model.callback.callback_queue_model import CallbackQueueModel
from model.wechat.wechat_file_model import WechatFileModel
from model.wechat.wechat_room_model import WechatRoomModel
from model.wechat.wechat_user_label_model import WechatUserLabelModel
from model.wechat.wechat_user_model import WechatUserModel
from model.wechat.wechat_msg_model import WechatMsgModel
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.core import Logger, Time, Error, Attr, Config, Str, Sys, Dir

logger = Logger()


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
            db = CallbackQueueModel()
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

    def callback_handler(self, params):
        """推送事件预处理"""
        res = {}
        logger.info(params['message'], 'VP_CALL_PAR')
        is_retry = params.get('is_retry', 0)  # 消息回放
        is_force = params.get('is_force', 0)  # 强制更新
        app_key = params.get('app_key')
        msg_id = params.get('message', {}).get('new_msg_id', 0)
        p_msg_id = params.get('message', {}).get('msg_id', 0)
        db = CallbackQueueModel()
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
            res['insert_db'] = pid = db.add_queue('wechatpad', params)
            logger.debug(res, 'VP_CALL_IDB')
        # 更新处理数据
        update_data = {"process_params": {"params": "[PAR]", "app_key": app_key}}
        res['update_db'] = db.update_process(int(pid), update_data)
        # 实际处理逻辑
        res['que_sub'] = self._callback_handler(pid=pid, params=params)
        return 'success' if res['que_sub'] else 'error'

    def _callback_handler(self, pid, params):
        """微信回调真正处理逻辑"""
        res = {"pid": pid}
        db = CallbackQueueModel()
        db.set_processed(pid)
        # 消息数据格式化
        res['rev_handler'], data = VpCallbackHandler.rev_handler(params)
        logger.debug(res['rev_handler'], 'VP_CALL_HD_RES')
        data['pid'] = pid
        # 消息指令处理 - 异步
        res['cmd_handler'] = RedisTaskQueue().add_task('VP_CM', data)
        # 消息数据入库 - 异步
        res['ins_handler'] = RedisTaskQueue().add_task('VP_IH', data)
        update_data = {"process_result": res, "process_params": data}
        if res['rev_handler']:
            update_data.update({"is_succeed": 1})
        res['update_db'] = db.update_process(int(pid), update_data)
        return res

    @staticmethod
    def command_handler(data):
        """微信消息指令处理入口"""
        try:
            app_key = data['app_key']
            is_at = data['is_at']
            is_my = data['is_my']
            s_wxid = data['send_wxid']
            g_wxid = data['g_wxid']
            content = data['content']
            use_at = 1
            if not(content and (is_at or is_my)):
                return False
            config = Config.vp_config()
            app_config = config['app_list'][app_key]
            # 拦截非允许群
            if g_wxid not in str(app_config['g_wxid']).split(','):
                return False
            room = WechatRoomModel().get_room_info(g_wxid)
            user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": s_wxid})
            s_wxid_name = user.get('display_name', '')
            s_user = {"id": s_wxid, "name": s_wxid_name}
            extra = {"g_wxid": g_wxid, "g_wxid_name": room.get('nickname', ''), "s_wxid": s_wxid, "s_wxid_name": s_wxid_name}
            commands = config['command_list'].split(',')
            content = Str.remove_at_user(content)
            if str(content).startswith(tuple(commands)):
                client = VpClient(app_key)
                redis = RedisClient()
                cache_key = 'LOCK_AI_VP_QUS'
                is_admin = s_wxid in str(config['admin_list']).split(',')
                if '1' == content:
                    response = '工号09527为您服务，提问请按101，百科请按102，任务请按201，红石请按202，其它请按103'
                elif '101' == content or str(content).startswith('#提问'):
                    if redis.get(cache_key, [s_wxid]) and not is_admin:
                        response = '每分钟只能提问一次'
                    else:
                        redis.set(cache_key, 1, [s_wxid])
                        content = '#提问' if '101' == content else content
                        response = AiCommandService.question(content, s_user, 'VP_QUS', extra)
                elif '102' == content or str(content).startswith('#百科'):
                    if redis.get(cache_key, [s_wxid]) and not is_admin:
                        response = '每分钟只能提问一次'
                    else:
                        redis.set(cache_key, 1, [s_wxid])
                        content = '#百科' if '102' == content else content
                        response = AiCommandService.science(content, s_user, 'VP_SCI', extra)
                elif '103' == content:
                    SendWxMsgService.send_qy_msg(app_key, f'{s_wxid_name} 正在呼唤你，请尽快回复')
                    response = '已发送至管理员……\r\n\r\n正在呼唤本人，请稍后……'
                    file = SkyDataService().get_sky_file('yj')
                    fp = file.get('save_path')
                    if fp:
                        fp = Dir.abs_dir(f'storage/upload/wechat/{fp}')
                        v_task = lambda path=fp, wxid=g_wxid: client.send_voice_message(path, wxid)
                        Sys.delayed_task(15, v_task)
                elif '201' == content or str(content).startswith('#任务'):
                    file = SkyDataService().get_sky_file('rw')
                    fp = file.get('save_path')
                    if fp:
                        fp = Dir.abs_dir(f'storage/upload/wechat/{fp}')
                        return client.send_img_msg(file.get('save_path'), g_wxid)
                    response = '获取sky任务失败'
                elif '202' == content or str(content).startswith('#红石'):
                    file = SkyDataService().get_sky_file('hs')
                    fp = file.get('save_path')
                    if fp:
                        fp = Dir.abs_dir(f'storage/upload/wechat/{fp}')
                        return client.send_img_msg(file.get('save_path'), g_wxid)
                    response = '获取sky红石失败'
                elif str(content).startswith('#公告'):
                    s_res = SkyDataService().get_sky_gg()
                    response = s_res.get('main', "暂未查询到公告")
                    use_at = 0
                elif str(content).startswith('#v50'):
                    s_res = SkyDataService().get_v50()
                    response = s_res.get('main', "暂未查询到v50")
                    use_at = 0
                elif str(content).startswith('#天气'):
                    city = str(content).replace('#天气', '').strip()
                    s_res = SkyDataService().get_weather(city)
                    response = s_res.get('main', "暂未查询到天气")
                    use_at = 0
                elif not is_admin:
                    # 拦截非管理员 - 以下功能都是只有管理员才能使用
                    response = '只有管理员才能使用该功能'
                elif str(content).startswith('#设置'):
                    response = '设置功能正在开发中……'
                elif str(content).startswith('#点歌'):
                    response = '点歌功能正在开发中……'
                elif str(content).startswith('#总结'):
                    response = '总结功能正在开发中……'
                else:
                    response = '暂未支持该功能……'
                at_list = [{"wxid": s_wxid, "nickname": s_wxid_name}] if use_at else []
                return client.send_msg(response, g_wxid, at_list)
            return False
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"消息指令处理失败 - {err}", "VP_CMD_ERR")
            return False

    @staticmethod
    def command_handler_retry(id_list):
        """微信消息指令处理重试"""
        return VpCallbackService._combine_handler_retry(id_list, 1)

    @staticmethod
    def insert_handler(data):
        """微信消息数据入库入口"""
        # 入库顺序： 群聊表 - 用户表 - 消息表
        try:
            res = {}
            app_key = data['app_key']
            msg_id = data['msg_id']
            pid = data['pid']
            msg_type = data['content_type']
            g_wxid = data['g_wxid']
            s_wxid = data['send_wxid']
            t_wxid = data['to_wxid']
            self_wxid = data['self_wxid']
            # 先判断消息有没有入库 - 已入库就不继续执行了
            mdb = WechatMsgModel()
            m_info = mdb.get_msg_info(msg_id)
            is_retry = data.get('is_retry')
            if m_info and not is_retry:
                return True
            # 内容为空 - 直接跳过
            if not data.get('content'):
                return False
            # 只有一个消费者，所以不用加锁
            client = VpClient(app_key)
            qdb = CallbackQueueModel()
            res['upd_cnt_1'] = qdb.set_retry_count(pid, 1)
            user_list = [{"wxid": s_wxid}, {"wxid": t_wxid}]
            room = {}
            # 群聊入库
            if g_wxid:
                room = client.get_room(g_wxid)
                rdb = WechatRoomModel()
                r_info = rdb.get_room_info(g_wxid)
                if not r_info:
                    res['ins_room'] = rdb.add_room(room, app_key)
                    r_info = rdb.get_room_info(g_wxid)
                if r_info and (Time.now() - Time.tfd(str(r_info['update_at'])) > 60):
                    res['chk_room'] = rdb.check_room_info(room, r_info)
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
            # 用户入库
            for u in user_list:
                wxid = u['wxid']
                user = client.get_user(wxid, g_wxid)
                user['user_type'] = 1 if user['is_friend'] else 2
                user['room_list'] = {g_wxid: room['nickname']} if room else {}
                u_info = Attr.select_item_by_where(u_list, {"wxid": wxid})
                if not u_info:
                    user['wx_nickname'] = user['nickname']
                    res['ins_user'] = udb.add_user(user, app_key)
                    u_info = udb.get_user_info(wxid)
                if u_info and (Time.now() - Time.tfd(str(u_info['update_at'])) > 60):
                    user['room_list'].update(u_info['room_list'])
                    res['chk_user'] = udb.check_user_info(user, u_info)
            # 文件下载 - 由于消息是单次入库的，所以文件下载就不用重复判断了
            fid = 0
            data['g_wxid_name'] = room['nickname'] if room else ''
            if msg_type in ['gif', 'png', 'mp4', 'file', 'voice']:
                file = client.download_file(data)
                if file['url']:
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
                r_msg = CallbackQueueModel().get_by_msg_id(r_msg_id)
                if r_msg:
                    data['content'] += f"<{r_msg['process_params']['content']}>"
            if m_info:
                res['upd_msg'] = mdb.add_msg(data, app_key, m_info['id'])
            else:
                res['ins_msg'] = mdb.add_msg(data, app_key)
            # 入库成功 - 更新队列表的 retry_count
            res['upd_cnt_2'] = qdb.set_retry_count(pid, 2)
            return res
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"消息入库失败 - {err}", "VP_INS_ERR")
            return False

    @staticmethod
    def insert_handler_retry(id_list):
        """微信消息数据入库重试"""
        return VpCallbackService._combine_handler_retry(id_list, 2)

    @staticmethod
    def _combine_handler_retry(id_list, r_type):
        """组合消息重试 - 多用于调试"""
        res = {}
        db = CallbackQueueModel()
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
