from tool.router.base_app import BaseApp
from service.wechat.callback.vp_command_service import VpCommandService


class VpMsg(BaseApp):

    _rule_list = {
        "send_msg": {
            "method": ["GET", "POST"],
            "rule": {
                "content": "required|string|max:999",
                "app_key": "string|in:a1,a2",
            }
        }
    }

    def send_msg(self):
        """通过链接发送微信消息"""
        content = self.params.get('content')
        commander = VpCommandService(self.app_key)
        res = commander.vp_normal_msg(content)
        return self.success(res)

