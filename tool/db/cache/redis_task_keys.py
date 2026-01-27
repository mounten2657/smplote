

class RedisTaskKeys:
    """redis 任务队列服务列表"""

    RTQ_QUEUE_LIST = {
        # wechatpad
        "VP_CH": {"s": "service.wechat.callback.vp_callback_service@VpCallbackService.callback_handler", "n": 4},
        # gpl batch
        "GPL_SYM": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol", "n": 4, "t": "batch"},
        "GPL_DAY": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol_daily", "n": 4, "t": "batch"},
        "GPL_EXT": {"s": "service.gpl.gpl_update_ext_service@GPLUpdateExtService.update_symbol_ext", "n": 4, "t": "batch"},
    }

