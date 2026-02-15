from threading import Semaphore
from tool.core import Logger, Env, Attr, Error, Time, Str
from tool.db.cache.redis_client import RedisClient
from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient

logger = Logger()
redis = RedisClient()


class VppClashService:
    """Vpp Clash API 集成封装"""

    # VPN 代理 - 多种合并
    _VPN_HOST = Env.get('PROXY_VPN_HOST')
    _VPN_AUTH = Env.get('PROXY_VPN_AUTH', '')
    _VPN_GROUP = Env.get('PROXY_VPN_GROUP', '')

    def __init__(self):
        self.client = VppServeClient()
        self.cache_key = 'PROXY_VPN_NODE'  # 节点缓存键
        self.port_list = self.get_vpn_port_list()   # list(range(781, 789))
        self.port_semaphores = {port: Semaphore(1) for port in self.port_list}  # 每个端口最多1个请求在执行

    def send_http_request(self, method, url, params=None, headers=None, proxy=None, timeout=None):
        """发起http请求并返回结果"""
        return self.client.cs7_http_req(method, url, params, headers, proxy, timeout)

    def get_vpn_host(self):
        """获取vpn主机地址"""
        return self._VPN_HOST

    def get_vpn_port_list(self):
        """获取vpn端口列表 - [781 ~ 789]"""
        p_list = self.get_vpn_e_port_list()
        p_list = [int(p) - 10 for p in p_list]  # 转换为代理接口
        return p_list

    def get_vpn_port(self,  is_refresh=0):
        """获取vpn端口 - [781 ~ 789]随机值"""
        p_list = self.get_vpn_port_list()
        # 从缓存中加载数据
        rand_list = redis.get(self.cache_key, [f'rand_list'])
        if not rand_list or is_refresh:
            rand_list = {}
            for port in p_list:
                num = redis.get(self.cache_key, [f'{port}:len'])
                num = int(num) if isinstance(num, int) else 0
                if num:  # 有节点才分配
                    rand_list[port] = num
            if not rand_list:  # 一个可用节点都没有
                Error.throw_exception('暂无缓存，请先初始化vpn节点')
            redis.set(self.cache_key, rand_list, [f'rand_list'])
        nc_list = Attr.nc_list(rand_list)
        return Attr.random_choice(nc_list)

    def get_vpn_url(self, port=0):
        """获取vpn链接"""
        if not port:
            return ''  # 兼容无代理情况
        return f"{self.get_vpn_host()}:{port}"

    def get_vpn_auth_header(self):
        """获取vpn认证header头"""
        return {"Authorization": f"Bearer {self._VPN_AUTH}"}

    def get_vpn_group_list(self):
        """获取vpn分组列表"""
        return Attr.parse_json_ignore(self._VPN_GROUP)

    def get_vpn_group_name(self, e_port):
        """获取vpn分组名"""
        gn_list = self.get_vpn_group_list()
        return gn_list[e_port]

    def get_vpn_e_port_list(self):
        """获取vpn api端口列表 - [791 ~ 799]"""
        gn_list = self.get_vpn_group_list()
        return list(gn_list.keys())

    def get_vpn_node(self, port, ctype='em'):
        """获取vpn节点 - 随机值"""
        n_list = redis.get(self.cache_key, [f'{port}:{ctype}'])  # 从缓存中读取
        if not n_list:
            return ''
        return Attr.random_choice(n_list)

    def init_vpn_node(self, p_list=None, is_refresh=1):
        """初始化vpn节点缓存 - 由定时器触发"""
        res = {'all': self.cache_vpn_node_all(p_list, is_refresh)}
        if res['all']:
            res['em'] = self.cache_vpn_node_em(p_list, is_refresh)
        return res

    def cache_vpn_node_all(self, p_list=None, is_refresh=0):
        """
        缓存vpn的节点池 - 全部节点

        :param p_list: 端口列表，不传就缓存所有端口
        :param is_refresh: 是否强制刷新
        :return: 成功操作的个数
        """
        i = 0
        p_list = p_list or self.get_vpn_e_port_list()
        for e_port in p_list:
            port = e_port - 10
            Time.sleep(Str.randint(1, 9) / 10)
            cache = redis.get(self.cache_key, [f'{port}:all'])
            if cache and not is_refresh:
                logger.warning(f"全节点缓存已存在<{port}>", "CVA_WAR")
                continue
            autoname = self.get_vpn_group_name(e_port)
            url = f"{self.get_vpn_host()}:{e_port}/proxies/{autoname}"
            headers = self.get_vpn_auth_header()
            res = self.send_http_request("GET", url, headers=headers)
            n_list = Attr.get_by_point(res, 'all')
            if not n_list:
                logger.warning(f"全节点列表获取失败<{url}>", "CVA_WAR")
                continue
            redis.set(self.cache_key, n_list, [f'{port}:all'])
            redis.set(self.cache_key, len(n_list), [f'{port}:tol'])
            logger.info(f"全节点缓存成功<{port}> - {len(n_list)}", "CVA_INF")
            i += 1
        return i

    def cache_vpn_node_em(self, p_list=None, is_refresh=0):
        """
        缓存vpn的节点池 - 东财可用节点

        :param p_list: 端口列表，不传就缓存所有端口
        :param is_refresh: 是否强制刷新
        :return: 成功操作的个数
        """
        i = 0
        p_list = p_list or self.get_vpn_e_port_list()
        ed = Time.date('%Y%m%d')
        sd = Time.dnd(ed, -30, '%Y%m%d')  # 向前推一个月必有数据
        em_url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        em_par = f"fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&beg={sd}&end={ed}&secid=0.300126"
        for e_port in p_list:
            port = e_port - 10
            Time.sleep(Str.randint(1, 9) / 10)
            cache = redis.get(self.cache_key, [f'{port}:em'])
            if cache and not is_refresh:
                logger.warning(f"东财节点缓存已存在<{port}>", "CVE_WAR")
                continue
            cache = redis.get(self.cache_key, [f'{port}:all'])
            if not cache or not isinstance(cache, list):
                logger.warning(f"请先刷新全节点缓存<{port}><{len(cache)}>", "CVE_WAR")
                continue
            node_list = []
            for node in cache:  # 轮询所有节点去请求东财
                # 过滤无效的节点
                if any(c in node for c in ['自动', '剩余', '到期', '故障', '直连', '文档', '客户端', '随机', '放假', '丢失', '频道', '订阅', '套餐', '网址', '请', 'Auto', 'auto']):
                    logger.warning(f"过滤无效节点<{port}><{node}>", "CVE_WAR")
                    continue
                if not self.switch_vpn_node(port, node, 1):
                    continue
                # 测试是否能从东财那里获取数据，能获取数据的才为真
                proxy = self.get_vpn_url(port)
                res = self.send_http_request("GET", em_url, em_par, None, proxy)
                if not Attr.get_by_point(res, 'data.klines'):
                    logger.warning(f"该节点无法获取东财数据<{port}><{node}> - {res}", "CVE_WAR")
                    continue
                logger.debug(f"该节点成功获取东财数据<{port}><{node}> - {res}", "CVE_DEG")
                node_list.append(node)
                Time.sleep(Str.randint(1, 9) / 10)
            redis.set(self.cache_key, node_list, [f'{port}:em'])
            redis.set(self.cache_key, len(node_list), [f'{port}:len'])
            logger.info(f"东财节点缓存成功<{port}> - {len(node_list)}", "CVE_INF")
            i += 1
        self.get_vpn_port(1)  # 刷新一下端口概率缓存
        return i

    def switch_vpn_node(self, port, node_name, sleep_time=None):
        """
        切换vpn的节点

        :param port: 代理端口
        :param node_name: 节点名称
        :param sleep_time: 休眠时间
        :return: 操作结果
        """
        e_port = port + 10  # 转换为 api 端口
        autoname = self.get_vpn_group_name(e_port)
        url = f"{self.get_vpn_host()}:{e_port}/proxies/{autoname}"
        params = {"name": node_name}
        headers = self.get_vpn_auth_header()
        res = self.send_http_request("PUT", url, params, headers)
        if res:
            logger.warning(f"策略组节点切换失败<{url}> - {params}", "GSN_WAR")
            return False
        logger.debug(f"策略组节点切换成功<{url}> - {params}", "GSN_DEG")
        if sleep_time:
            Time.sleep(Str.randint(3, 9) / 10 + sleep_time)
        return True

    def send_http_request_pro(self, method, url, params=None, headers=None, port=None, node=None, ctype='em', timeout=None):
        """发起http请求改进版 - 节点利用最大化 - 同端口请求串行化"""
        port = int(port)
        if not port:  # 代理端口必传
            Error.throw_exception(f'empty port - {url} - {params}')
        # 使用 Semaphore 确保同一端口的请求串行
        with self.port_semaphores[port]:
            proxy = self.get_vpn_url(port)
            if not node:
                node = self.get_vpn_node(port, ctype) # 随机选出一个可用节点并切换过去
                if not node:
                    Error.throw_exception(f'empty node cache - {url} - {proxy} - {params}')
            self.switch_vpn_node(port, node, 0.1)  # 给切换节点一点反应时间
            return self.send_http_request(method, url, params, headers, proxy, timeout)
