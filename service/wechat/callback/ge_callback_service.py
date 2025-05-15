from tool.core import *
from utils.wechat.gewechat.ge_client import GeClient
from utils.wechat.gewechat.callback.wechat_callback_handler import WechatCallbackHandler
from model.callback.callback_queue_model import CallbackQueueModel

logger = Logger()


class GeCallbackService(Que):

    @staticmethod
    def reset_callback():
        """重置回调链接"""
        return GeClient.set_gewechat_callback()

    def callback_handler(self, params):
        """推送事件入队列"""
        res = {}
        logger.info(params, 'GE_CALL_PAR')
        db = CallbackQueueModel()
        # 数据入库
        res['insert_db'] = pid = db.add_queue('gewechat', params)
        logger.debug(res, 'GE_CALL_IDB')
        method = Http.get_request_method()
        # 更新处理数据
        update_data = {"process_params": {"method": method}}
        res['update_db'] = db.update_process(int(pid), update_data)
        # 入队列
        res['que_sub'] = self.que_submit(pid=pid, method=method)
        return 'success' if res['que_sub'] else 'error'

    def _que_exec(self, **kwargs):
        """队列执行入口"""
        pid = kwargs.get('pid')
        method = kwargs.get('method')
        return self._callback_handler(pid, method)


    @staticmethod
    def _callback_handler(pid, method):
        """微信回调入口"""
        # 自动转到 GET 或 POST 方法
        res = {}
        db = CallbackQueueModel()
        db.set_processed(pid)
        callback_handler = WechatCallbackHandler()
        method = getattr(callback_handler, method)
        res['msg_handler'] = method()
        update_data = {"process_result": res}
        if res['msg_handler'] == 'success':
            update_data.update({"is_succeed": 1})
        res['update_db'] = db.update_process(int(pid), update_data)
        return res

    @staticmethod
    def callback_handler_after(result, msg):
        """消息处理完后的回调 - 主要是入库 - 继续使用队列处理"""
        logger.info({"res": result, 'msg': msg}, 'GE_CALL_AFTER_PAR')
        return True

