from tool.router.base_app import BaseApp
from service.webhook.gitee_callback_handler import GiteeCallbackHandler


class GiteeCallback(BaseApp):

    _rule_list = {
        "smplote": {
            "method": ["POST"],
            "rule": {
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
        res = GiteeCallbackHandler.push_handler(self.params)
        return self.success(res)