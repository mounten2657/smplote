from tool.core import Http, Error, Logger, Api, Attr, Env
from tool.db.cache.redis_client import RedisClient

logger = Logger()
redis = RedisClient()


class VppPxqService:
    """携趣代理池方法封装"""
    
    # IP代理服务商信息
    _XQ_OPT_URL = Env.get('PROXY_OPT_URL_XQ')
    _XQ_OPT_UID = Env.get('PROXY_OPT_UID_XQ')
    _XQ_OPT_KEY = Env.get('PROXY_OPT_KEY_XQ')
    _XQ_URL = Env.get('PROXY_API_URL_XQ')
    _XQ_UID = Env.get('PROXY_API_UID_XQ')
    _XQ_KEY = Env.get('PROXY_API_KEY_XQ')

    @staticmethod
    def init_proxy():
        """
        代理初始化

        :return: 初始化结果
        """
        res = {}
        url = 'http://ip.sb'
        headers = {"User-Agent": "curl/7.68.0"}
        # 获取本地IP
        res['ip'] = str(Http.send_request('GET', url, headers=headers, proxy='')).strip()
        if not res['ip']:
            return Api.error(f"Get local ip failed: {url}")
        url = f"{VppPxqService._XQ_OPT_URL}/IpWhiteList.aspx"
        params = {
            "uid": VppPxqService._XQ_OPT_UID,
            "ukey": VppPxqService._XQ_OPT_KEY,
        }
        # 获取代理白名单中的IP列表
        res['get'] = Http.send_request('GET', url, params | {"act": "getjson"})  # {"data":[{"IP":"x.x.x.x","MEMO":""}]}
        if not res['get']:
            return Api.error(f"Get white ip failed: {res['get']}")
        # 白名单中没有备注的都是程序设置的iP
        wip = ''
        wd = Attr.get_by_point(res["get"], 'data')
        for w in wd:
            if not w.get('MEMO'):
                wip = w.get('IP')
                break
        if not (len(wd) == 1 and not wip):  # not 没有本地ip
            if not wip or wip == res["ip"]:
                return res
            # 删除老IP
            res['del'] = Http.send_request('GET', url, params | {"act": "del", "ip": wip})  # success
            if not res['del']:
                return Api.error(f"Get white ip failed: {res['del']}")
        # 添加本地IP到白名单中
        res['add'] = Http.send_request('GET', url, params | {"act": "add", "ip": res['ip']})  # success
        if not res['add']:
            return Api.error(f"Get white ip failed: {res['add']}")
        return res

    @staticmethod
    def get_proxy_cache(n=200):
        """从代理池缓存中获取一个代理"""
        proxy_key = "PROXY_POOL_LIST"  # 列表键，过期时间两分钟
        lock_key = "PROXY_POOL_LOCK"  # 列表锁键
        min_threshold = 8  # 列表长度小于该值时触发刷新
        try:
            # 检查当前代理列表长度，不足则加锁刷新
            current_len = redis.l_len(proxy_key)
            if current_len < min_threshold:
                # 加分布式锁避免死锁
                if redis.set_nx(lock_key, "locked"):
                    # 二次检查长度（防止锁等待期间已被其他线程刷新）
                    if redis.l_len(proxy_key) < min_threshold:
                        new_proxies = VppPxqService.get_proxy(n)  # 拉取新的代理
                        if new_proxies:
                            redis.delete(proxy_key)  # 清空旧列表
                            redis.l_push(proxy_key, new_proxies)  # 批量写入新代理
                    redis.delete(lock_key)  # 释放锁
            # 原子操作弹出一个代理
            proxy = redis.r_pop(proxy_key)
            if not proxy:  # 极端情况：弹出为空（列表被取完），再次刷新并尝试获取
                if redis.set_nx(lock_key, "locked"):
                    new_proxies = VppPxqService.get_proxy(n)
                    if new_proxies:
                        redis.delete(proxy_key)
                        redis.l_push(proxy_key, new_proxies)
                        proxy = redis.r_pop(proxy_key)
                    redis.delete(lock_key)
        except Exception as e:
            err = Error.handle_exception_info(e)
            logger.error(f"获取代理缓存异常 - {err}", 'PPC_ERR')
            proxy = ''
        return proxy[0] if isinstance(proxy, list) else proxy

    @staticmethod
    def get_proxy_tunnel(pn=0):
        """
        随机获取代理隧道池编号

        :param int pn: 隧道池编号
        :return: 隧道号
        """
        if pn:
            return int(pn)
        # {隧道池编号: 数量} - 确保数量多的隧道被选中的概率最高
        number_counts = {
            51: 535,  # J池 - 53.5%
            82: 140,  # D池
            57: 135,  # B池
            61: 130,  # Z池
            62: 50,  # X池
            76: 10  # X池 （三分钟版）
        }
        number_list = Attr.nc_list(number_counts)
        return Attr.random_choice(Attr.random_list(number_list))

    @staticmethod
    def get_proxy(num=1, pn=0):
        """
        获取代理ip
         - 文档地址 - https://12qk8h1t7l.apifox.cn/323203443e0

        :param int num: 提取个数，一个时返回字符串，多个时返回列表
        :param int pn: 隧道池编号
        :return: 代理ip
        """
        ip_list = []
        url = f"{VppPxqService._XQ_URL}/VAD/GetIp.aspx"
        pn = 51 if num >= 200 else pn # 只有 J 池数量才管够
        tn = VppPxqService.get_proxy_tunnel(pn)  # 从所有的隧道池中随机取出一个
        params = {
            "act": f"getturn{tn}",
            "uid": VppPxqService._XQ_UID,
            "vkey": VppPxqService._XQ_KEY,
            "time": 6,
            "plat": 0,
            "re": 0,
            "type": 7,
            "so": 1,
            "group": 51,
            "ow": 1,
            "spl": 1,
            "addr": "",
            "db": 1,
            "num": num
        }
        res = Http.send_request('GET', url, params)  # {"code":0,"success":"true","msg":"","data":[{"IP":"x.x.x.x","Port":5639,"IpAddress":"Unknow"}]}
        ret = Attr.get_by_point(res, 'data', [])
        for r in ret:
            if r.get('IP') and r.get('Port'):
                ip = f"http://{r['IP']}:{r['Port']}"
                ip_list.append(ip)
        if not ip_list:
            return '' if num == 1 else []
        return ip_list[0] if num == 1 else ip_list
    