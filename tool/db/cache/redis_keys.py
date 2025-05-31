

class RedisKeys:
    """redis 缓存键列表"""

    # 字符串类型
    CACHE_KEY_STRING = {
        # 锁相关
        "LOCK_RTQ_CNS": {"key": "lock_redis_consumer", "ttl": 87400},
        "LOCK_SQL_CNT": {"key": "lock_mysql_connection", "ttl": 87400},
        "LOCK_WSS_CNT": {"key": "lock_wss_connection", "ttl": 87400},
        # 微信用户相关
        "VP_USER_INFO": {"key": "wechatpad:user:base_info:%s", "ttl": 3600},
        "VP_USER_FRD_INF": {"key": "wechatpad:user:frd_info:%s", "ttl": 3600},
        "VP_USER_FRD_RAL": {"key": "wechatpad:user:frd_relation:%s", "ttl": 86400},
        "VP_USER_FRD_LAB": {"key": "wechatpad:user:frd_label", "ttl": 7 * 86400},
        "VP_USER_DB_INF": {"key": "wechatpad:user:frd_label", "ttl": 3600},
        # 微信群聊相关
        "VP_ROOM_INFO": {"key": "wechatpad:room:base_info:%s", "ttl": 3600},
        "VP_ROOM_GRP_INF": {"key": "wechatpad:room:grp_info:%s", "ttl": 7 * 86400},
        "VP_ROOM_GRP_USL": {"key": "wechatpad:room:grp_users:%s", "ttl": 3600},
        "VP_ROOM_GRP_NTC": {"key": "wechatpad:room:grp_notice:%s", "ttl": 86400},
    }



