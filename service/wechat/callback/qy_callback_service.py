from tool.core import Logger, Str, Que, Time, Http
from tool.db.cache.redis_client import RedisClient
from utils.wechat.qywechat.callback.qy_verify_handler import QyVerifyHandler
from utils.wechat.qywechat.callback.qy_callback_handler import QyCallbackHandler
from model.callback.callback_queue_model import CallbackQueueModel

logger = Logger()


class QyCallbackService(Que):

    def callback_handler(self, app_key, params):
        """推送事件入队列"""
        res = {}
        # 加锁去重
        Time.sleep(Str.randint(1, 20) / 10)
        md5 = Str.md5(str(params))
        if not RedisClient().set_nx('LOCK_QY_CAL', 1, [md5]):
            return 'error'
        logger.info(params, 'QY_CALL_PAR')
        db = CallbackQueueModel()
        # 数据入库
        res['insert_db'] = pid = db.add_queue('qyapi', params)
        logger.debug(res, 'QY_CALL_IDB')
        if Http.get_request_method() == 'GET':
            # 初始化验证 - 一般只走一次 - 验证就不走队列了，需要实时返回
            res['verify'] = QyVerifyHandler.verify(app_key)
            if res['verify']:
                update_data = {"process_result": res, "is_processed": 1, "is_succeed": 1}
                db.update_process(int(pid), update_data)
            return res['verify']
        xml = params.get('xml', '')
        # 更新处理数据
        update_data = {"process_params": {"app_key": app_key, "xml": '[XML]'}}
        res['update_db'] = db.update_process(int(pid), update_data)
        if len(xml) == 0:
            return 'invalid request'
        # 入队列
        res['que_sub'] = self.que_submit(pid=pid, app_key=app_key, xml=xml)
        return 'success' if res['que_sub'] else 'error'

    def _que_exec(self, **kwargs):
        """队列执行入口"""
        pid = kwargs.get('pid')
        app_key = kwargs.get('app_key')
        xml = kwargs.get('xml')
        return self._callback_handler(pid, app_key, xml)

    @staticmethod
    def _callback_handler(pid, app_key, xml):
        """推送事件处理"""
        res = {}
        db = CallbackQueueModel()
        db.set_processed(pid)
        res['msg_handler'], data = QyCallbackHandler.msg_handler(app_key, xml)
        update_data = {"process_result": res, "process_params": data}
        if res['msg_handler']:
            update_data.update({"is_succeed": 1})
        res['update_db'] = db.update_process(int(pid), update_data)
        return res

