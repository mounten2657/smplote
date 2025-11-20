from tool.router.base_app_vp import BaseAppVp
from service.wechat.reply.vp_msg_service import VpMsgService


class VpMsg(BaseAppVp):

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
        res = VpMsgService.vp_normal_msg(content, None, self.g_wxid, self.app_key)
        return self.success(res)

