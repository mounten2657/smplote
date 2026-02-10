from tool.core import Http, Error, Logger, Str, Time, Api, Attr, Env
from tool.db.cache.redis_client import RedisClient
from service.vps.open_nat_service import OpenNatService
from service.vpp.vpp_serve_service import VppServeService

logger = Logger()
redis = RedisClient()


class NatService:
    """网络请求分发类"""

    # IP代理服务商 - 携趣
    _XQ_OPT_URL = Env.get('PROXY_OPT_URL_XQ')
    _XQ_OPT_UID = Env.get('PROXY_OPT_UID_XQ')
    _XQ_OPT_KEY = Env.get('PROXY_OPT_KEY_XQ')
    _XQ_URL = Env.get('PROXY_API_URL_XQ')
    _XQ_UID = Env.get('PROXY_API_UID_XQ')
    _XQ_KEY = Env.get('PROXY_API_KEY_XQ')

    # VPN 代理 - 多种合并
    _VPN_HOST = Env.get('PROXY_VPN_HOST')
    _VPN_PORT = Env.get('PROXY_VPN_PORT', '')

    # 混合模式下各种请求的概率
    _PROXY_RAND = Env.get('PROXY_RAND', '')

    def ppr_request(self, method, url, params, headers=None, proxy=None):
        """利用代理池发起请求"""
        if not proxy:
            proxy = self.get_proxy_cache()
            if not proxy:
                Error.throw_exception('获取代理池失败，请检查缓存或代理商白名单')
        return Http.send_request(method, url, params, headers, proxy)

    def vpn_request(self, method, url, params, headers=None, port=None, timeout=None):
        """利用vpn发起请求"""
        proxy = self.get_vpn_url(port)
        return VppServeService.send_http_request(method, url, params, headers, proxy, timeout)

    def vps_request(self, method, url, params, headers=None):
        """利用vps发起请求"""
        return OpenNatService.send_http_request(method, url, params, headers)

    def mixed_request(self, method: str, url: str, params=None, headers=None, retry_times=9):
        """
        发送HTTP请求 - 混合模式，各种模式随机请求
          - 此模式下每次发起请求的IP基本不会相同，适合于高频爬取网站数据
          - 请求失败默认重试九次

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :param retry_times: 失败的重试次数
        :return: json | str | err , r_type, proxy
        """
        res = {}
        port = 0
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
                    proxy = self.get_proxy_cache()
                    res = self.ppr_request(method, url, params, headers, proxy)
                elif r_type == 'v':  # VPN - 10% --> 90%
                    port = self.get_vpn_port()  # 随机端口
                    proxy = self.get_vpn_url(port)
                    redis.incr(total_key, [f'{data}:cnt_{port}'])
                    res = self.vpn_request(method, url, params, headers, port)
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
                par = {"r": r_type, "i": i, "o": port, "x": proxy, "m": method,  "u": url, "p": params, "h": headers, "e": err}
                if i < retry_times - 1:
                    logger.warning(f"请求失败，重试中<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_WAR')
                    redis.incr(total_key, [f'{data}:war'])
                    redis.incr(total_key, [f'{data}:war_{port}'])
                    if port:
                        redis.incr(failed_key, [f"{data}:{uuid}_w"])
                        redis.set_nx(failed_key, par, [f"{data}:{uuid}_w_{i}"])
                    Time.sleep(5 +  i * 4)  # 稍微等待一下，总计152秒，而节点刷新时间为2分钟
                else:
                    logger.error(f"请求错误，已超过最大重试次数<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_ERR')
                    redis.incr(total_key, [f'{data}:fal'])
                    redis.incr(total_key, [f'{data}:fal_{port}'])
                    redis.incr(failed_key, [f"{data}:{uuid}_e"])
                    redis.set_nx(failed_key, par, [f"{data}:{uuid}_e_{i}"])
                    return err, r_type, proxy
        return res, r_type, proxy

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
        url = f"{NatService._XQ_OPT_URL}/IpWhiteList.aspx"
        params = {
            "uid": NatService._XQ_OPT_UID,
            "ukey": NatService._XQ_OPT_KEY,
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
                        new_proxies = NatService.get_proxy(n)  # 拉取新的代理
                        if new_proxies:
                            redis.delete(proxy_key)  # 清空旧列表
                            redis.l_push(proxy_key, new_proxies)  # 批量写入新代理
                    redis.delete(lock_key)  # 释放锁
            # 原子操作弹出一个代理
            proxy = redis.r_pop(proxy_key)
            if not proxy:  # 极端情况：弹出为空（列表被取完），再次刷新并尝试获取
                if redis.set_nx(lock_key, "locked"):
                    new_proxies = NatService.get_proxy(n)
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
        url = f"{NatService._XQ_URL}/VAD/GetIp.aspx"
        pn = 51 if num >= 200 else pn # 只有 J 池数量才管够
        tn = NatService.get_proxy_tunnel(pn)  # 从所有的隧道池中随机取出一个
        params = {
            "act": f"getturn{tn}",
            "uid": NatService._XQ_UID,
            "vkey": NatService._XQ_KEY,
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

    @staticmethod
    def get_vpn_port():
        """获取vpn端口 - 随机值"""
        nc_list = Attr.nc_list(Attr.parse_json_ignore(NatService._VPN_PORT))
        return Attr.random_choice(nc_list)  # 781 ~ 789

    @staticmethod
    def get_vpn_url(port=0):
        """获取vpn链接"""
        if port == 0:
            return ''  # 兼容无代理情况
        return f"{NatService._VPN_HOST}:{port}"

    @staticmethod
    def get_mixed_rand():
        """获取混合模式下的随机值"""
        nc_list = Attr.nc_list(Attr.parse_json_ignore(NatService._PROXY_RAND))
        return Attr.random_choice(nc_list)  # l, z, v, x

