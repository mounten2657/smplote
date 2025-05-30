from utils.wechat.vpwechat.vp_client import VpClient
from utils.wechat.vpwechat.callback.vp_callback_handler import VpCallbackHandler
from model.callback.callback_queue_model import CallbackQueueModel
from model.wechat.wechat_file_model import WechatFileModel
from tool.db.cache.redis_task_queue import RedisTaskQueue
from tool.core import Logger, Time

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
        return True

    @staticmethod
    def command_handler_retry(id_list):
        """微信消息指令处理重试"""
        return VpCallbackService._combine_handler_retry(id_list, 1)

    @staticmethod
    def insert_handler(data):
        """微信消息数据入库入口"""
        return True

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
            if 1 == r_type:
                res[pid] = VpCallbackService.command_handler(queue['process_params'])
            else:
                res[pid] = VpCallbackService.insert_handler(queue['process_params'])
            Time.sleep(0.1)
        return res
