from service.wechat.callback.vp_command_service import VpCommandService
from service.wechat.callback.vp_callback_service import VpCallbackService
from service.gpl.gpl_update_service import GPLUpdateService
from tool.router.base_app_vp import BaseAppVp
from tool.core import Time, Sys, Http


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
        def sky_task_exec(gid, sid, method, *args):
            client = VpCommandService(app_key, gid, sid)
            func = getattr(client, method, None)
            if not func or not callable(func):
                raise ValueError(f"不存在的vp方法: {method}")
            return func(*args)
        for g_wxid in g_list:
            res[g_wxid] = {}
            res[g_wxid]['vp_sky_rw'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_sky_rw')
            res[g_wxid]['vp_sky_hs'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_sky_hs', '', 1)
            res[g_wxid]['vp_xw'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_xw', delay_seconds=40)
            res[g_wxid]['vp_ov_wa'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_ov_wa', delay_seconds=50)
        return self.success(res)

    def vp_msg(self):
        """vp消息重试 - 每小时的第10分钟"""
        if Time.is_night():
            return self.success(True)
        ids = self.params.get('ids', '-1')
        res = self.vp.callback_handler_retry(self.app_key, {"ids": ids})
        return self.success(res)

    def vp_room(self):
        """刷新群聊的信息 - 每小时的第58分钟"""
        if Time.is_night():
            return self.success(True)
        g_wxid_str = self.params.get('g_wxid_str', '')
        res = self.vp.refresh_room_info(self.app_key, g_wxid_str)
        return self.success(res)

    def vp_log(self):
        """清理历史日志 - 每天上午的06点06分"""
        res = self.vp.clear_api_log()
        return self.success(res)

    def rf_proxy(self):
        """刷新代理服务 - 每小时的第11分钟"""
        res = Http.init_proxy()
        return self.success(res)

    def gpl_info(self):
        """更新股票基础信息 - 每天凌晨的01点11分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        td = self.params.get('td', '')
        res = self.gpl.quick_update_symbol(code_str, int(is_force), 'GPL_SYM', td)
        return self.success(res)

    def gpl_ext(self):
        """更新股票额外信息 - 每天凌晨的04点11分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        td = self.params.get('td', '')
        res = self.gpl.quick_update_symbol(code_str, int(is_force), 'GPL_EXT', td)
        return self.success(res)

    def gpl_daily(self):
        """更新股票额外信息 - 每天下午的15点31分和21点01分"""
        code_str = self.params.get('code_str', '')
        is_force = self.params.get('is_force', 0)
        td = self.params.get('td', '')
        res = self.gpl.quick_update_symbol(code_str, int(is_force), 'GPL_DAY', td)
        return self.success(res)
