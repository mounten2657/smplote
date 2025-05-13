from tool.core import *
from tool.unit.md.gitee_webhook_md import GiteeWebhookMd
from utils.wechat.qywechat.qy_client import QyClient

logger = Logger()


class GiteeWebhook:

    @staticmethod
    def push_handler(params):
        """推送事件处理"""
        res = {}
        logger.debug(params.get('hook_name'), 'GITEE_PUSH_PAR')
        status, data = GiteeWebhookMd.get_push_md()
        logger.debug(status, 'GITEE_PUSH_STU')
        if status == 200 and 'markdown' in data:
            # 发送企业应用消息
            res['app_msg'] = QyClient().send_msg(data['markdown'])
            # 其它异步流程
        return res

