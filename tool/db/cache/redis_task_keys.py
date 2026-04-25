

class RedisTaskKeys:
    """redis 任务队列服务列表"""

    RTQ_QUEUE_LIST = {
        # wechatpad
        "VP_CH": {"s": "service.wechat.callback.vp_callback_service@VpCallbackService.vp_callback_handler", "n": 2, "t": "vp"},
        # qy wechat
        "QY_CAL": {"s": "service.wechat.callback.qy_callback_service@QyCallbackService.qy_push_handler", "n": 2, "t": "vp"},
        # gpl batch
        "GPL_SYM": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol", "n": 1, "t": "gpl_sym"},
        "GPL_EXT": {"s": "service.gpl.gpl_update_ext_service@GPLUpdateExtService.update_symbol_ext", "n": 1, "t": "gpl_ext"},
        "GPL_DAY": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol_daily", "n": 2, "t": "gpl_day"},
        "GPL_DAY_VPN": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol_daily", "n": 4, "t": "gpl_day_vpn"},
    }

