from utils.wechat.vpwechat.vp_client import VpClient
from utils.wechat.vpwechat.callback.vp_callback_handler import VpCallbackHandler
from model.callback.callback_queue_model import CallbackQueueModel
from tool.core import Logger, Que

logger = Logger()


class VpCallbackService(Que):

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

    def callback_handler(self, params):
        """推送事件入队列"""
        res = {}
        logger.info(params['message'], 'VP_CALL_PAR')
        app_key = params.get('app_key')
        msg_id = params.get('message', {}).get('new_msg_id', 0)
        db = CallbackQueueModel()
        # msg_id 唯一 - 已入库就跳过
        info = db.get_by_msg_id(msg_id)
        if info:
            logger.warning(f"消息已入库 - 跳过 - {msg_id}", 'VP_CALL_SKP')
            return 'success'
        # 数据入库
        res['insert_db'] = pid = db.add_queue('wechatpad', params)
        logger.debug(res, 'VP_CALL_IDB')
        # 更新处理数据
        update_data = {"process_params": {"params": "[PAR]", "app_key": app_key}}
        res['update_db'] = db.update_process(int(pid), update_data)
        # 入队列
        res['que_sub'] = self.que_submit(pid=pid, params=params)
        return 'success' if res['que_sub'] else 'error'

    def _que_exec(self, **kwargs):
        """队列执行入口"""
        pid = kwargs.get('pid')
        params = kwargs.get('params')
        return self._callback_handler(pid, params)

    @staticmethod
    def _callback_handler(pid, params):
        """微信回调真正处理逻辑"""
        res = {}
        db = CallbackQueueModel()
        db.set_processed(pid)
        # 消息数据格式化
        res['rev_handler'], data = VpCallbackHandler.rev_handler(params)
        logger.debug(res['rev_handler'], 'VP_CALL_HD_RES')
        # 消息数据入微信库
        # do something
        update_data = {"process_result": res, "process_params": data}
        if res['rev_handler']:
            update_data.update({"is_succeed": 1})
        res['update_db'] = db.update_process(int(pid), update_data)
        return res


