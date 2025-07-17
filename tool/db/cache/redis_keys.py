

class RedisKeys:
    """redis 缓存键列表"""

    # 字符串类型
    CACHE_KEY_STRING = {
        # 锁相关
        "LOCK_SYS_CNS": {"key": "lock_sys_consumer:%s", "ttl": 120},
        "LOCK_RTQ_CNS": {"key": "lock_redis_consumer:%s", "ttl": 87400},
        "LOCK_SQL_CNT": {"key": "lock_mysql_connection", "ttl": 87400},
        "LOCK_WSS_CNT": {"key": "lock_wss_connection", "ttl": 87400},
        "LOCK_AI_VP_QUS": {"key": "lock_ai_vp_qus:%s", "ttl": 60},
        "LOCK_SKY_API_SG": {"key": "lock_sky_api_sg:%s", "ttl": 60},
        "LOCK_QY_MSG": {"key": "lock_qy_msg:%s", "ttl": 60},
        "LOCK_QY_CAL": {"key": "lock_qy_msg:%s", "ttl": 60},
        "LOCK_WS_ON_ERR": {"key": "lock_ws_on_err", "ttl": 60},
        # 微信用户相关
        "VP_USER_INFO": {"key": "wechatpad:user:base_info:%s", "ttl": 86400},
        "VP_USER_FRD_INF": {"key": "wechatpad:user:frd_info:%s", "ttl": 86400},
        "VP_USER_FRD_RAL": {"key": "wechatpad:user:frd_relation:%s", "ttl": 86400},
        "VP_USER_FRD_LAB": {"key": "wechatpad:user:frd_label", "ttl": 86400},
        # 微信群聊相关
        "VP_ROOM_INFO": {"key": "wechatpad:room:base_info:%s", "ttl": 86400},
        "VP_ROOM_GRP_INF": {"key": "wechatpad:room:grp_info:%s", "ttl": 86400},
        "VP_ROOM_GRP_USL": {"key": "wechatpad:room:grp_users:%s", "ttl": 86400},
        "VP_ROOM_GRP_NTC": {"key": "wechatpad:room:grp_notice:%s", "ttl": 86400},
        "VP_ROOM_USR_LOCK": {"key": "wechatpad:room:usr_lock:%s", "ttl": 3600},
        # sky 接口相关
        "SKY_OVO_RW": {"key": "sky:ovo:rw", "ttl": 'today'},
        "SKY_OVO_DJS": {"key": "sky:ovo:djs", "ttl": 'today'},
        # gpl 业务相关
        "GPL_STOCK_CODE_LIST": {"key": "gpl:stock:code_list", "ttl": 86400},
        "GPL_STOCK_TD_LIST": {"key": "gpl:stock:td_list", "ttl": 'today'},
        "GPL_STOCK_INFO_XQ": {"key": "gpl:stock:xq:%s", "ttl": 'today'},
        "GPL_STOCK_INFO_EM": {"key": "gpl:stock:em:%s", "ttl": 'today'},
    }



