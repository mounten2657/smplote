from tool.router.base_app import BaseApp
from service.gitee.gitee_webhook_service import GiteeWebhookService


class GiteeCallback(BaseApp):

    _rule_list = {
        "smplote": {
            "method": ["POST"],
            "rule": {
                "hook_name": "required",
                "repository": "required",
                "ref": "required",
                "pusher": "required",
                "compare": "required",
                "commits": "required",
            }
        }
    }

    def smplote(self):
        """gitee 项目代码推送回调处理 - smplote"""
        res = GiteeWebhookService().push_handler(self.params)
        return self.success(res)