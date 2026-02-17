from service.wechat.callback.vp_command_service import VpCommandService
from service.wechat.callback.vp_callback_service import VpCallbackService
from service.gpl.gpl_update_service import GPLUpdateService
from service.vpp.vpp_pxq_service import VppPxqService
from service.vpp.vpp_clash_service import VppClashService
from tool.router.base_app_vp import BaseAppVp
from tool.core import Time, Sys


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
        i = 0
        for g_wxid in g_list:
            ad = int(i == 0)  # 是否为管理员群
            res[g_wxid] = {}
            # res[g_wxid]['vp_good_morning'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_good_morning', delay_seconds=0.1 + i) if not ad else 0 # > 10
            # res[g_wxid]['vp_rank'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_rank', '#昨日榜', delay_seconds=10 + i) if not ad else 0  # > 20  # 反响不好，暂时屏蔽
            res[g_wxid]['vp_xw'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_xw', '', 0, delay_seconds=30 + i) if ad else 0  # > 15  # 0: 仅新闻 | 1: 新闻 + 历史上的今天
            # res[g_wxid]['vp_sky_rl'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_sky_rl', '', 2, delay_seconds=45 + i) if not ad else 0 # > 15  # 管理员群不发
            # res[g_wxid]['vp_sky_rw'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_sky_rw', '', 2, delay_seconds=60 + i) # > 40  # 0: 仅任务图片 | 1: 所有任务相关图片 | 2: 文字版 | 20: 图片+文字 | 21: 所有图片+文字
            # res[g_wxid]['vp_sky_hs'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_sky_hs', '', 2, delay_seconds=100 + i) # > 30  # 0: 图片(每天发) | 1: 图片(仅周末发) | 2: 文字版(仅周末发)
            res[g_wxid]['vp_ov_wa'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_ov_wa', delay_seconds=130 + i) if ad else 0  # > 15
            res[g_wxid]['vp_ov_bz'] = Sys.delayed_task(sky_task_exec, g_wxid, s_wxid, 'vp_ov_bz', '', 2, delay_seconds=145 + i) if ad else 0  # > 20  # # 壁纸类型：1:二次元 | 2:必应 | 3:cosplay
            i += 120
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
        res = {}
        res['vp'] = self.vp.clear_api_log()
        res['gpl'] = self.gpl.clear_api_log()
        return self.success(res)

    def rf_proxy(self):
        """刷新代理服务 - 每小时的第11分钟"""
        res = VppPxqService.init_proxy()
        return self.success(res)

    def rf_node(self):
        """刷新vpn节点 - 每天凌晨的00点15分"""
        ports = self.params.get('p', '')  # 是代理端口不是api端口
        if not ports and 6 <= Time.week():
            return self.error('周末不执行')
        p_list = [int(p) + 10 for p in ports.split(',')] if ports else []  # 转为api端口
        res = Sys.delayed_task(VppClashService().init_vpn_node, p_list, timeout=3600)
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
