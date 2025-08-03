from service.wechat.callback.vp_command_service import VpCommandService
from service.wechat.callback.vp_callback_service import VpCallbackService
from service.gpl.gpl_update_service import GPLUpdateService
from tool.router.base_app_vp import BaseAppVp
from tool.core import Sys, Time


class Task(BaseAppVp):
    """定时任务控制器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vp = VpCallbackService
        self.gpl = GPLUpdateService()

    def sky_rw(self):
        """sky任务 - 每天上午的06点36分"""
        res = {}
        app_key = self.app_key
        s_wxid = self.wxid
        g_list = self.g_wxid_list.split(',')
        for g_wxid in g_list:
            client = VpCommandService(app_key, g_wxid, s_wxid)
            res[g_wxid] = {
                "vp_sky_rw": client.vp_sky_rw(),
                "vp_sky_hs": client.vp_sky_hs(),
            }
        return self.success(res)

    def vp_msg(self):
        """vp消息重试 - 每小时的10分"""
        if Time.is_night():
            return self.success(True)
        res = self.vp.callback_handler_retry(self.app_key, {"ids": "-1"})
        return self.success(res)

    def vp_room(self):
        """刷新群聊的信息 - 十五分钟一次"""
        if Time.is_night():
            return self.success(True)
        g_wxid_str = self.params.get('g_wxid_str', '')
        res = self.vp.refresh_room_info(self.app_key, g_wxid_str)
        return self.success(res)

    def vp_log(self):
        """清理历史日志 - 每天上午的06点06分"""
        res = self.vp.clear_api_log()
        return self.success(res)

    def gpl_info(self):
        """更新股票基础信息 - 每天上午的01点11分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        res = self.gpl.quick_update_symbol(code_str, int(is_force), 'GPL_SYM')
        return self.success(res)

    def gpl_ext(self):
        """更新股票额外信息 - 每天下午的02点44分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        res = self.gpl.quick_update_symbol(code_str, int(is_force), 'GPL_SAF')
        return self.success(res)

    def gpl_daily(self):
        """更新股票额外信息 - 每天上午的15点31分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        res = self.gpl.quick_update_symbol(code_str, int(is_force), 'GPL_DAY')
        return self.success(res)
