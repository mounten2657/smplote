from tool.core import *
from utils.wechat.gewechat.ge_client import GeClient
from utils.wechat.gewechat.callback.wechat_callback_handler import WechatCallbackHandler
from model.callback.callback_queue_model import CallbackQueueModel

logger = Logger()


class GeCallbackService(Que):

    def reset_callback(self):
        """重置回调链接"""
        return GeClient().set_gewechat_callback()

    def callback_handler(self, params):
        """推送事件入队列"""
        res = {}
        logger.info(params, 'GE_CALL_PAR')
        db = CallbackQueueModel()
        # 数据入库
        res['insert_db'] = pid = db.add_queue('gewechat', params)
        logger.debug(res, 'GE_CALL_IDB')
        # 更新处理数据
        update_data = {"process_params": {"params": params}}
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
        """微信回调入口"""
        res = {}
        db = CallbackQueueModel()
        db.set_processed(pid)
        res['msg_handler'] = WechatCallbackHandler().ge_handler(params)
        update_data = {"process_result": res}
        if res['ge_handler']:
            update_data.update({"is_succeed": 1})
        res['update_db'] = db.update_process(int(pid), update_data)
        return res


