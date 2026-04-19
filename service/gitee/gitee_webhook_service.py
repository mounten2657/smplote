from tool.core import Logger, Config, Sys
from tool.unit.md.gitee_webhook_md import GiteeWebhookMd
from utils.wechat.qywechat.qy_client import QyClient
from model.callback.callback_queue_model import CallbackQueueModel

logger = Logger()


class GiteeWebhookService():

    def push_handler(self, params):
        """推送事件入队列"""
        res = {}
        logger.debug(params.get('hook_name'), 'GITEE_PUSH_PAR')
        db = CallbackQueueModel()
        # 数据入库
        res['insert_db'] = pid = db.add_queue('gitee', params)
        logger.debug(res, 'GITEE_PUSH_IDB')
        # 整理 md 文本
        status, data = GiteeWebhookMd.get_push_md()
        logger.debug(status, 'GITEE_PUSH_STU')
        # 更新处理数据
        update_data = {"process_params": {"status": status, "data": data}}
        res['update_db'] = db.update_process(int(pid), update_data)
        # 入队列 - 改为同步了
        res['que_sub'] = GiteeWebhookService.gitee_push_handler(pid, status, data)
        return res

    @staticmethod
    def gitee_push_handler(pid, status, data):
        """推送事件处理"""
        res = {}
        update_data = {}
        db = CallbackQueueModel()
        db.set_processed(pid)
        if status == 200 and 'markdown' in data:
            # 发送企业应用消息
            res['send_msg'] = QyClient().send_msg(data['markdown'])
            if Config.is_prod():
                # 延迟拉取最新代码并重启 flask
                res['git_pull'] = Sys.delayed_task(Sys.delay_reload_gu, delay_seconds=3)
            # 更新处理结果
            update_data['process_result'] = res
            if res['send_msg']:
                update_data['is_succeed'] = 1
            res['update_db'] = db.update_process(int(pid), update_data)
        return res.get('git_pull', '0')
