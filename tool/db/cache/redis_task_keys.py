

class RedisTaskKeys:
    """redis 任务队列服务列表"""

    RTQ_QUEUE_LIST = {
        # wechatpad
        "VP_CH": {"s": "service.wechat.callback.vp_callback_service@VpCallbackService.vp_callback_handler", "n": 4, "t": "vp"},
        # qy wechat
        "QY_CAL": {"s": "service.wechat.callback.qy_callback_service@QyCallbackService.qy_push_handler", "n": 4, "t": "vp"},
        "QY_GIT": {"s": "service.gitee.gitee_webhook_service@GiteeWebhookService.gitee_push_handler", "n": 4, "t": "vp"},
        # gpl batch
        "GPL_SYM": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol", "n": 4, "t": "gpl"},
        "GPL_DAY": {"s": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol_daily", "n": 4, "t": "gpl"},
        "GPL_EXT": {"s": "service.gpl.gpl_update_ext_service@GPLUpdateExtService.update_symbol_ext", "n": 4, "t": "gpl"},
    }

