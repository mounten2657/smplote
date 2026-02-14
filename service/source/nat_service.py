from tool.core import Http, Error, Logger, Str, Time, Attr, Env
from tool.db.cache.redis_client import RedisClient
from service.vpp.vpp_pxq_service import VppPxqService
from service.vpp.vpp_clash_service import VppClashService
from service.vps.open_nat_service import OpenNatService

logger = Logger()
redis = RedisClient()


class NatService:
    """网络请求分发类"""

    # 混合模式下各种请求的概率
    _PROXY_RAND = Env.get('PROXY_RAND', '')

    def __init__(self):
        self.ppr = VppPxqService()
        self.vpn = VppClashService()
        self.vps = OpenNatService()

    def ppr_request(self, method, url, params=None, headers=None, proxy=None):
        """利用代理池发起请求"""
        if not proxy:
            proxy = self.ppr.get_proxy_cache()
            if not proxy:
                Error.throw_exception('获取代理池失败，请检查缓存或代理商白名单')
        return Http.send_request(method, url, params, headers, proxy)

    def vpp_request(self, method, url, params=None, headers=None, port=None, timeout=None):
        """利用vpp发起请求"""
        proxy = self.vpn.get_vpn_url(port)
        return self.vpn.send_http_request(method, url, params, headers, proxy, timeout)

    def vps_request(self, method, url, params=None, headers=None):
        """利用vps发起请求"""
        return self.vps.send_http_request(method, url, params, headers)

    def mixed_request(self, method: str, url: str, params=None, headers=None, retry_times=5):
        """
        发送HTTP请求 - 混合模式
          - 各种模式随机请求，由配置文件决定概率
          - 此模式下每次发起请求的IP基本不会相同，适合于高频爬取网站数据
          - 请求失败默认重试5次

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :param retry_times: 失败的重试次数
        :return: json | str | err , r_type, proxy
        """
        res = {}
        port = 0
        node = ''
        proxy = ''
        uuid = Str.uuid()
        data = Time.date('%Y-%m-%d')
        r_type = self.get_mixed_rand()
        total_key = "PROXY_STAT_TOL"  # 总数统计
        failed_key = "PROXY_STAT_FAL"  # 失败统计
        redis.incr(total_key, ['sig'])
        for i in range(0, retry_times):
            r_type = self.get_mixed_rand() if i else r_type
            redis.incr(total_key, [f'{data}:cnt'])
            redis.incr(total_key, [f'{data}:cnt_{r_type}'])
            try:
                if r_type == 'x':  # 代理池 - 80%  --> 0%   # 收费太贵且效果不佳，暂不考虑
                    proxy = self.ppr.get_proxy_cache()
                    res = self.ppr_request(method, url, params, headers, proxy)
                elif r_type == 'v':  # VPN - 10% --> 90%
                    port = self.vpn.get_vpn_port()  # 随机端口
                    node = self.vpn.get_vpn_node(port)  # 随机节点
                    proxy = self.vpn.get_vpn_url(port)
                    redis.incr(total_key, [f'{data}:cnt_{port}'])
                    res = self.vpn.send_http_request_pro(method, url, params, headers, port, node)  # 使用进阶版，节点最大化利用
                elif r_type == 'z':   # VPS - 5%
                    proxy = 'vps'
                    res = self.vps_request(method, url, params, headers)
                else:  # 本地 - 5%
                    proxy = '_'
                    res = Http.send_request(method, url, params, headers)
                if proxy and r_type in ('x', 'x'):
                    logger.info(f"代理请求<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params}", 'MIXED_INF')
                if str(res).startswith('HTTP request failed'):
                    Error.throw_exception(res)
                redis.incr(total_key, [f'{data}:suc'])
                redis.incr(total_key, [f'{data}:suc_{port}'])
                return res, r_type, proxy
            except Exception as e:
                err = Error.handle_exception_info(e)
                par = {"r": r_type, "i": i, "o": port, "n": node, "x": proxy, "m": method,  "u": url, "p": params, "h": headers, "e": err}
                if i < retry_times - 1:
                    logger.warning(f"请求失败，重试中<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_WAR')
                    redis.incr(total_key, [f'{data}:war'])
                    redis.incr(total_key, [f'{data}:war_{port}'])
                    if port:
                        redis.incr(failed_key, [f"{data}:{uuid}_w"])
                        redis.set_nx(failed_key, par, [f"{data}:{uuid}_w_{i}"])
                    Time.sleep(5 +  i * 12)  # 稍微等待一下，总计145秒，而节点刷新时间为2分钟
                else:
                    logger.error(f"请求错误，已超过最大重试次数<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_ERR')
                    redis.incr(total_key, [f'{data}:fal'])
                    redis.incr(total_key, [f'{data}:fal_{port}'])
                    redis.incr(failed_key, [f"{data}:{uuid}_e"])
                    redis.set_nx(failed_key, par, [f"{data}:{uuid}_e_{i}"])
                    return err, r_type, proxy
        return res, r_type, proxy

    def get_mixed_rand(self):
        """获取混合模式下的随机值 - [l, z, v, x]"""
        nc_list = Attr.nc_list(Attr.parse_json_ignore(self._PROXY_RAND))
        return Attr.random_choice(nc_list)

