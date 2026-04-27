from threading import Semaphore
from tool.core import Logger, Env, Attr, Error, Time, Str, Http, File
from tool.db.cache.redis_client import RedisClient
from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient

logger = Logger()
redis = RedisClient()
today = Time.dnd()
tomorrow = Time.dnd(1)  # 节点缓存时复刻明日以兼容凌晨获取节点失败问题


class VppClashService:
    """Vpp Clash API 集成封装"""

    # VPN 代理 - 多种合并
    _VPN_HOST = Env.get('PROXY_VPN_HOST')
    _VPN_AUTH = Env.get('PROXY_VPN_AUTH', '')
    _VPN_GROUP = Env.get('PROXY_VPN_GROUP', '')
    _VPN_SUB_LIST = Env.get('PROXY_VPN_SUB_LIST', '')
    _VPN_SUB_FILE = Env.get('PROXY_VPN_SUB_FILE', '')

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
        rand_list = redis.get(self.cache_key, [f'rand_list:{today}'])
        if not rand_list or is_refresh:
            rand_list = {}
            for port in p_list:
                num = redis.get(self.cache_key, [f'{port}:{today}:len'])
                num = int(num) if isinstance(num, int) else 0
                rand_list[port] = num  # 不管有没有节点都记录
            if not sum(rand_list.values()):  # 一个可用节点都没有
                Error.throw_exception('暂无缓存，请先初始化vpn节点')
            redis.set(self.cache_key, rand_list, [f'rand_list:{today}'])
            redis.set(self.cache_key, rand_list, [f'rand_list:{tomorrow}'])
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

    def get_vpn_sub_list(self):
        """获取vpn订阅列表"""
        sub_list = Attr.parse_json_ignore(self._VPN_SUB_LIST)
        # 从YAML文件中读取真实的配置信息 - 保证配置来源的唯一性
        url_list = Str.extract_url(File.read_file(self._VPN_SUB_FILE))
        u_list = []
        for i, url in enumerate(url_list):
            if i in [0, 3, 10, 11]  or i > 11:
                continue
            u_list.append(url)
        u_list.reverse()
        for k, v in sub_list.items():
            sub_list[k] = u_list.pop()
        return sub_list

    def get_vpn_group_name(self, e_port):
        """获取vpn分组名"""
        gn_list = self.get_vpn_group_list()
        return gn_list[e_port]

    def get_vpn_e_port_list(self):
        """获取vpn api端口列表 - [791 ~ 799]"""
        gn_list = self.get_vpn_group_list()
        return list(gn_list.keys())

    def get_vpn_node(self, port, c_type='em'):
        """获取vpn节点 - 随机值"""
        n_list = redis.get(self.cache_key, [f'{port}:{today}:{c_type}'])  # 从缓存中读取
        if not n_list:
            return ''
        n_list = self.filter_invalid_node(n_list, port)
        return Attr.random_choice(n_list)

    def filter_invalid_node(self, node_list, port=None):
        """过滤无效节点"""
        n_list = []
        filter_list = ['自动', '剩余', '到期', '故障', '直连', '文档', '客户端', '随机', '放假', '丢失', '频道', '订阅', '套餐', '网址', '邮箱', '请', 'Auto', 'auto']
        for node in node_list:
            if any(c in node for c in filter_list):
                logger.warning(f"过滤无效节点<{port}><{node}>", "CVE_WAR")
                continue
            n_list.append(node)
        return n_list

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
            cache = redis.get(self.cache_key, [f'{port}:{today}:all'])
            if cache and not is_refresh:
                logger.warning(f"全节点缓存已存在<{port}>", "CVA_WAR")
                continue
            auto_name = self.get_vpn_group_name(e_port)
            url = f"{self.get_vpn_host()}:{e_port}/proxies/{auto_name}"
            headers = self.get_vpn_auth_header()
            res = self.send_http_request("GET", url, headers=headers)
            n_list = Attr.get_by_point(res, 'all')
            if not n_list:
                logger.warning(f"全节点列表获取失败<{url}>", "CVA_WAR")
                continue
            redis.set(self.cache_key, n_list, [f'{port}:{today}:all'])
            redis.set(self.cache_key, n_list, [f'{port}:{tomorrow}:all'])
            redis.set(self.cache_key, len(n_list), [f'{port}:{today}:tol'])
            redis.set(self.cache_key, len(n_list), [f'{port}:{tomorrow}:tol'])
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
        sd = Time.dnd(-30, ed, '%Y%m%d')  # 向前推一个月必有数据
        em_url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
        em_par = f"fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&beg={sd}&end={ed}&secid=0.300126"
        for e_port in p_list:
            port = e_port - 10
            Time.sleep(Str.randint(1, 9) / 10)
            cache = redis.get(self.cache_key, [f'{port}:{today}:em'])
            if cache and not is_refresh:
                logger.warning(f"东财节点缓存已存在<{port}>", "CVE_WAR")
                continue
            cache = redis.get(self.cache_key, [f'{port}:{today}:all'])
            if not cache or not isinstance(cache, list):
                logger.warning(f"请先刷新全节点缓存<{port}>", "CVE_WAR")
                continue
            node_list = []
            cache = self.filter_invalid_node(cache, port)
            if not cache:
                continue
            for node in cache:  # 轮询所有节点去请求东财
                # 测试是否能从东财那里获取数据，能获取数据的才为真
                if not self.switch_vpn_node(port, node, 1):
                    continue
                proxy = self.get_vpn_url(port)
                res = self.send_http_request("GET", em_url, em_par, None, proxy)
                if not Attr.get_by_point(res, 'data.klines'):
                    logger.warning(f"该节点无法获取东财数据<{port}><{node}> - {res}", "CVE_WAR")
                    continue
                logger.info(f"该节点成功获取东财数据<{port}><{node}> - {res}", "CVE_DEG")
                Time.sleep(Str.randint(1, 9) / 10)
                node_list.append(node)
            redis.set(self.cache_key, node_list, [f'{port}:{today}:em'])
            redis.set(self.cache_key, len(node_list), [f'{port}:{today}:len'])
            redis.set(self.cache_key, node_list, [f'{port}:{tomorrow}:em'])
            redis.set(self.cache_key, len(node_list), [f'{port}:{tomorrow}:len'])
            logger.info(f"东财节点缓存成功<{port}> - {len(node_list)}", "CVE_INF")
            i += 1
            try:
                self.get_vpn_port(1)  # 每次都刷新一下端口概率缓存 - 即使第一次报错也无所谓，有后面的兜底
            except Exception as e:
                logger.warning(f"该订阅无可用节点<{port}> - {e}", "CVE_WAR")
                continue
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
        auto_name = self.get_vpn_group_name(e_port)
        url = f"{self.get_vpn_host()}:{e_port}/proxies/{auto_name}"
        params = {"name": node_name}
        headers = self.get_vpn_auth_header()
        res = self.send_http_request("PUT", url, params, headers)
        if res:
            logger.warning(f"策略组节点切换失败<{url}> - {params} - {res}", "GSN_WAR")
            return False
        logger.debug(f"策略组节点切换成功<{url}> - {params}", "GSN_DEG")
        if sleep_time:
            Time.sleep(Str.randint(3, 9) / 10 + sleep_time)
        return True

    def send_http_request_pro(self, method, url, params=None, headers=None, port=None, node=None, timeout=None):
        """发起http请求改进版 - 节点利用最大化 - 同端口请求串行化"""
        port = int(port)
        if not port:  # 代理端口必传
            Error.throw_exception(f'empty port - {url} - {params}')
        # 使用 Semaphore 确保同一端口的请求串行
        with self.port_semaphores[port]:
            proxy = self.get_vpn_url(port)
            if not node:  # 传入的节点为空才会进入这个逻辑
                node = self.get_vpn_node(port, 'all') # 随机选出一个节点并切换过去
                if not node:
                    Error.throw_exception(f'empty node cache - {url} - {proxy} - {params}')
            self.switch_vpn_node(port, node, 0.1)  # 给切换节点一点反应时间
            return self.send_http_request(method, url, params, headers, proxy, timeout)

    def get_traffic_stat(self, sn=None):
        """获取订阅流量统计 - md文本"""
        def get_rvl_sum(d):
            rand_list = redis.get(self.cache_key, [f'rand_list:{d}'])
            rvl = [v for k, v in rand_list.items() if k != '784'] if isinstance(rand_list, dict) else []  # 去除免费节点
            rvs = sum(int(r) for r in rvl) if rvl else 0
            rvs = rvs if rvs else 10000  # 空值兼容
            rvl.reverse()  # 倒序以方便弹出r
            return rvl, rvs
        t_stat = {}
        yesterday = Time.dnd(-1)
        # 加载今昨节点数
        rv_list, rv_sum = get_rvl_sum(today)
        rv_list_y, rv_sum_y = get_rvl_sum(yesterday)
        # 加载昨日流量统计
        y_stat = redis.get(self.cache_key, [f'traffic_stat:{yesterday}'])
        sub_list = self.get_vpn_sub_list()
        md = f"🚀VPN节点流量统计🌐 <{today}>\r\n"
        if sn:
            if not sub_list.get(sn):
                return f"无效的订阅名 - {sn}"
            sub_list = {sn: sub_list[sn]}
        for sub, url in sub_list.items():
            stat = Http.get_subscription_traffic(url)
            if isinstance(stat, dict):
                t_stat[sub] = stat
                np = rv_list.pop() if rv_list else 0
                npy = rv_list_y.pop() if rv_list_y else 0
                used = Str.round(stat['upload'] + stat['download'])
                t_stat[sub]['used'] = used
                y_used = Attr.get_by_point(y_stat, f'{sub}.used', 0)
                changed = Str.round(used - y_used)
                t_stat[sub]['changed'] = changed
                used = f"{round(used / 1024, 3):.3f}G" if used >= 1024 else f"{used:.2f}M"
                stat = f"{changed}M/{used}/{stat['total']}G | {npy}/{np}/{rv_sum} | {stat['expire'] if stat['expire'] else 9999}天 "
            md += f"   - {sub}: {stat}\r\n"
        # 更新今日统计缓存
        redis.set(self.cache_key,  t_stat, [f'traffic_stat:{today}'])
        return md.strip()

