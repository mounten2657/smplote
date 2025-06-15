

class RedisTaskKeys:
    """redis 任务队列服务列表"""

    RTQ_SERVICE_LIST = {
        # wechatpad 相关
        "VP_CH": "service.wechat.callback.vp_callback_service@VpCallbackService.callback_handler",
        "VP_CM": "service.wechat.callback.vp_callback_service@VpCallbackService.command_handler",
        "VP_IH": "service.wechat.callback.vp_callback_service@VpCallbackService.insert_handler",
        "VP_USR": "service.wechat.callback.vp_callback_service@VpCallbackService.update_user",
    }

