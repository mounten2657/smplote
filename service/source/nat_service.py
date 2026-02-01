from tool.core import Http, Error, Logger, Str
from tool.db.cache.redis_client import RedisClient
from service.vps.open_nat_service import OpenNatService

logger = Logger()


class NatService:
    """网络请求分发类"""

    def __init__(self):
        self.redis = RedisClient()

    def proxy_pool_request(self, method, url, params, headers=None):
        """利用代理池发起请求"""
        return Http.send_request_x(method, url, params, headers)

    def vpn_request(self, method, url, params, headers=None):
        """利用vpn发起请求"""
        return Http.send_request_v(method, url, params, headers)

    def vps_request(self, method, url, params, headers=None):
        """利用vps发起请求"""
        return OpenNatService.send_http_request(method, url, params, headers)

    def get_proxy_cache(self, n=200):
        """从代理池缓存中获取一个代理"""
        redis = self.redis
        min_threshold = 8  # 列表长度小于该值时触发刷新
        proxy_key = "PROXY_POOL_LIST"  # 列表键，过期时间两分钟
        lock_key = "PROXY_POOL_LOCK"  # 列表锁键
        try:
            # 检查当前代理列表长度，不足则加锁刷新
            current_len = redis.l_len(proxy_key)
            if current_len < min_threshold:
                # 加分布式锁避免死锁
                if redis.set_nx(lock_key, "locked"):
                    # 二次检查长度（防止锁等待期间已被其他线程刷新）
                    if redis.l_len(proxy_key) < min_threshold:
                        new_proxies = Http.get_proxy(n)  # 拉取新的代理
                        if new_proxies:
                            redis.delete(proxy_key)  # 清空旧列表
                            redis.l_push(proxy_key, new_proxies)  # 批量写入新代理
                    redis.delete(lock_key)  # 释放锁
            # 原子操作弹出一个代理
            proxy = redis.r_pop(proxy_key)
            if not proxy:  # 极端情况：弹出为空（列表被取完），再次刷新并尝试获取
                if redis.set_nx(lock_key, "locked"):
                    new_proxies = Http.get_proxy(n)
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

    def mixed_request(self, method: str, url: str, params=None, headers=None, retry_times=3):
        """
        发送HTTP请求
          - 请求失败默认重试三次
          - 混合模式，各种模式随机请求
          - 此模式下每次发起请求的IP基本不会相同，适合于高频爬取网站数据

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :param retry_times: 失败的重试次数
        :return: json | str | err , r_type, proxy
        """
        res = {}
        proxy = ''
        r_type = Http.get_mixed_rand()
        uuid = Str.uuid()
        for i in range(0, retry_times):
            r_type = Http.get_mixed_rand() if i else r_type
            try:
                if r_type == 'x':  # 代理池 - 80%
                    proxy = self.get_proxy_cache()
                    if not proxy:
                        Error.throw_exception('获取代理池失败，请检查缓存或代理商白名单')
                    res = Http.send_request(method, url, params, headers, proxy)
                elif r_type == 'v':  # VPN - 10%
                    proxy = Http.get_vpn_url()
                    res = Http.send_request(method, url, params, headers, proxy)
                elif r_type == 'z':   # VPS - 5%
                    proxy = 'vps'
                    res = self.vps_request(method, url, params, headers)
                else:  # 本地 - 5%
                    proxy = '_'
                    res = Http.send_request(method, url, params, headers)
            except Exception as e:
                err = Error.handle_exception_info(e)
                if i < retry_times - 1:
                    logger.warning(f"请求失败<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_WAR')
                else:
                    logger.error(f"请求错误，已超过最大重试次数<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_ERR')
                    return err, r_type, proxy
        return res, r_type, proxy

