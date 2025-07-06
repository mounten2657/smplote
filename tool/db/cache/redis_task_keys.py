

class RedisTaskKeys:
    """redis 任务队列服务列表"""

    RTQ_QUEUE_LIST = [
        # wechatpad
        'rtq_vp_ch1_queue', 'rtq_vp_ch2_queue', 'rtq_vp_ch3_queue', 'rtq_vp_ch4_queue',
        'rtq_vp_ih1_queue', 'rtq_vp_ih2_queue', 'rtq_vp_ih3_queue', 'rtq_vp_ih4_queue',
        'rtq_vp_cm_queue',
        'rtq_vp_usr_queue',
        'rtq_gpl_sym1_queue', 'rtq_gpl_sym2_queue', 'rtq_gpl_sym3_queue', 'rtq_gpl_sym4_queue',
        'rtq_gpl_saf1_queue', 'rtq_gpl_saf2_queue', 'rtq_gpl_saf3_queue', 'rtq_gpl_saf4_queue',
    ]

    RTQ_SERVICE_LIST = {
        # wechatpad
        "VP_CH": "service.wechat.callback.vp_callback_service@VpCallbackService.callback_handler",
        "VP_IH": "service.wechat.callback.vp_callback_service@VpCallbackService.insert_handler",
        "VP_CM": "service.wechat.callback.vp_callback_service@VpCallbackService.command_handler",
        "VP_USR": "service.wechat.callback.vp_callback_service@VpCallbackService.update_user",
        # gpl
        "GPL_SYM": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol",
        "GPL_SAF": "service.gpl.gpl_update_service@GPLUpdateService.update_symbol_ext",
    }

