from service.wechat.callback.vp_command_service import VpCommandService
from service.wechat.callback.vp_callback_service import VpCallbackService
from tool.router.base_app_vp import BaseAppVp
from tool.core import Sys


class Task(BaseAppVp):
    """定时任务控制器"""

    def sky_rw(self):
        """sky任务 - 每天上午的六点"""
        app_key = self.app_key
        g_wxid = self.g_wxid
        s_wxid = self.wxid
        client = VpCommandService(app_key, g_wxid, s_wxid)
        tasks = {
            "vp_sky_rw": lambda: client.vp_sky_rw(),
            "vp_sky_hs": lambda: client.vp_sky_hs(),
        }
        res = {name: Sys.delayed_task(1, task) for name, task in tasks.items()}
        return self.success(res)

    def vp_msg(self):
        """vp消息重试 - 每小时的10分"""
        res = VpCallbackService.callback_handler_retry(self.app_key, {"ids": "-1"})
        return self.success(res)
