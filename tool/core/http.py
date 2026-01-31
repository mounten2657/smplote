import re
import json
import requests
import itertools
import uuid
import time
import random
from flask import request
from urllib.parse import urlencode, urlparse
from typing import Union, Dict, Optional
from tool.core.attr import Attr
from tool.core.env import Env
from tool.core.api import Api


class Http:

    # IP代理服务商 - 携趣
    _XQ_OPT_URL = Env.get('PROXY_OPT_URL_XQ')
    _XQ_OPT_UID = Env.get('PROXY_OPT_UID_XQ')
    _XQ_OPT_KEY = Env.get('PROXY_OPT_KEY_XQ')

    # VPN 代理 - 多种合并
    _VPN_URL = Env.get('PROXY_VPN_URL')
    _VPN_PORT = Env.get('PROXY_VPN_PORT')
    _VPN_RAND = Env.get('PROXY_VPN_RAND')

    # 混合模式下各种请求的概率
    _PROXY_RAND = Env.get('PROXY_RAND')

    # 雪球财经相关配置
    _XQ_URL = Env.get('PROXY_API_URL_XQ')
    _XQ_UID = Env.get('PROXY_API_UID_XQ')
    _XQ_KEY = Env.get('PROXY_API_KEY_XQ')

    @staticmethod
    def get_random_headers():
        """
        生成随机的仿浏览器请求头 - 避免被识别为爬虫

        @return: dict - 随机请求头
        """
        # 随机UA
        user_agents = [
            # Chrome - Windows 不同版本
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Chrome - macOS 不同版本
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Firefox - 不同系统/版本
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            # Edge - 不同版本
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            # Safari - 不同版本
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            # 随机值
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
        ]
        # 随机语言
        accept_languages = [
            "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "zh-CN,zh;q=0.9",
            "zh-CN,zh;q=0.8,en-US;q=0.7,en;q=0.6",
            "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
        ]
        # 随机Referer
        referer = [
            "https://quote.eastmoney.com/",
            "https://www.eastmoney.com/",
            "https://finance.eastmoney.com/",
            "https://www.baidu.com/",
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://www.zhihu.com/",
            "https://www.sina.com.cn/",
            "https://www.163.com/",
            None, None, None, None, None, None,  # 随机无Referer
        ]
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": random.choice([
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "text/html,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "application/json, text/plain, */*",
                "application/json;q=0.9,*/*;q=0.8",
            ]),
            "Accept-Language": random.choice(accept_languages),
            "Accept-Encoding": random.choice([
                "gzip, deflate, br",
                "gzip, deflate",
                "br, gzip, deflate"
            ]),
            "Connection": random.choice(["keep-alive", "close"]),
            "Cache-Control": random.choice([
                "max-age=0",
                "no-cache",
                "no-store, max-age=0",
                "private, max-age=0"
            ]),
        }
        # 可选属性 - 低概率
        if random.random() < 0.3:
            headers["DNT"] = random.choice(["1", "0"])
        if random.random() < 0.2:
            headers["Upgrade-Insecure-Requests"] = "1"
        if random.random() < 0.4:
            headers["X-Request-Id"] = str(uuid.uuid4())
        if random.random() < 0.3:
            headers["X-Requested-With"] = "XMLHttpRequest"
        if random.random() < 0.2:
            headers["X-Timestamp"] = str(int(time.time()))
        # sec 谨慎添加 - 超低概率
        if random.random() < 0.01:
            # 随机Sec-CH-UA
            sec_ch_ua_list = [
                '"Not_A Brand";v="8", "Chromium";v="121", "Microsoft Edge";v="121"',
                '"Google Chrome";v="121", "Not:A-Brand";v="8", "Chromium";v="121"',
                '"Microsoft Edge";v="120", "Chromium";v="120", "Not.A/Brand";v="24"',
                '"Firefox";v="122", "Not=A?Brand";v="99"'
            ]
            # 随机Sec-CH-UA-Platform
            sec_ch_ua_platform = [
                '"Windows"',
                '"macOS"',
                '"Linux"'
            ]
            # 可选的额外头
            optional_headers = {
                "X-Requested-With": ["XMLHttpRequest", "com.android.browser"],
                "Sec-Fetch-Site": ["none", "same-origin", "cross-site"],
                "Sec-Fetch-Mode": ["navigate", "no-cors", "cors"],
                "Sec-Fetch-Dest": ["document", "empty", "iframe"],
                "Sec-Fetch-User": ["?1", None],  # 随机有无
                "Priority": ["u=0, i", "u=1, i", None],  # 优先级头
                "Sec-CH-UA-Mobile": ["?0", "?1"],  # 移动端/桌面端
                "If-Modified-Since": [time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()), None]  # 缓存头
            }
            headers = headers | {
                "Sec-CH-UA": random.choice(sec_ch_ua_list),
                "Sec-CH-UA-Platform": random.choice(sec_ch_ua_platform),
                "Sec-CH-UA-Mobile": random.choice(optional_headers["Sec-CH-UA-Mobile"]),
                "Sec-Fetch-Dest": random.choice(optional_headers["Sec-Fetch-Dest"]),
                "Sec-Fetch-Mode": random.choice(optional_headers["Sec-Fetch-Mode"]),
                "Sec-Fetch-Site": random.choice(optional_headers["Sec-Fetch-Site"])
            }
        # 随机Referer（可能为空）
        referer = random.choice(referer)
        if referer:
            headers["Referer"] = referer
        # 返回headers
        return headers

    @staticmethod
    def send_request(
            method: str,
            url: str,
            params: Union[Dict, str, None] = None,
            headers: Optional[Dict] = None,
            proxy = None
    ) -> Union[Dict, str]:
        """
        发送HTTP请求并自动处理JSON响应

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :param proxy: 代理
        :return: 如果响应是JSON则返回字典，否则返回原始文本
        :raises:
            ValueError: 方法不支持或参数无效
            requests.exceptions.RequestException: 请求失败
        """
        # 参数校验
        method = method.upper()
        if method not in ('GET', 'POST', 'JSON', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
            raise ValueError(f"Unsupported HTTP method: {method}")
        if not url:
            raise ValueError("URL cannot be None")

        # 初始化请求参数
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers or {},
            'timeout': 120,
        }
        # 新增代理
        if proxy is not None:
            request_kwargs['proxies'] = {'http': proxy, 'https': proxy}

        # 处理params参数
        params_str = None
        if isinstance(params, dict):
            params_str = urlencode(params)
        elif isinstance(params, str):
            params_str = params if '=' in params else None

        if 'GET' == method:
            request_kwargs.update({
                'params': params_str
            })
        elif 'JSON' == method:
            request_kwargs.update({
                'method': 'POST',
                'json': params,
            })
        else:
            request_kwargs.update({
                'data': params_str
            })

        # 发送请求
        try:
            rep = requests.request(**request_kwargs)
            rep.raise_for_status()  # 检查HTTP错误

            # 自动处理JSON响应
            if 'application/json' in rep.headers.get('Content-Type', ''):
                return rep.json()
            return Attr.parse_json_ignore(rep.text)

        except (json.JSONDecodeError,requests.exceptions.RequestException) as e:
            raise requests.exceptions.RequestException(
                f"HTTP request failed: {str(e)}"
            ) from e

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
        url = f"{Http._XQ_OPT_URL}/IpWhiteList.aspx"
        params = {
            "uid": Http._XQ_OPT_UID,
            "ukey": Http._XQ_OPT_KEY,
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
        number_list = list(itertools.chain.from_iterable(
            [num] * count for num, count in number_counts.items()
        ))
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
        url = f"{Http._XQ_URL}/VAD/GetIp.aspx"
        tn = Http.get_proxy_tunnel(pn)  # 从所有的隧道池中随机取出一个
        params = {
            "act": f"getturn{tn}",
            "uid": Http._XQ_UID,
            "vkey": Http._XQ_KEY,
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
    def send_request_x(
            method: str,
            url: str,
            params: Union[Dict, str, None] = None,
            headers: Optional[Dict] = None,
    ) -> Union[Dict, str]:
        """
        发送HTTP请求并自动处理JSON响应
          - 代理模式，确保每次请求的ip都不同

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :return: 如果响应是JSON则返回字典，否则返回原始文本
        """
        proxy= Http.get_proxy(1)
        if not proxy:
            return Api.error(f"Get http proxy failed: {proxy}")
        return Http.send_request(method, url, params, headers, proxy)

    @staticmethod
    def get_vpn_count():
        """获取vpn总数"""
        return len(Http._VPN_PORT.split(','))

    @staticmethod
    def get_vpn_url(i=0):
        """获取vpn链接 - 对外提供的方法"""
        port_list = Http._VPN_PORT.split(',')
        rand_list = Http._VPN_RAND.split(',')
        rand_list = rand_list if len(rand_list) > 0 else list(range(1, len(port_list) + 1))  # 优先以自己指定的概率为准
        i = int(i if i else Attr.random_choice(rand_list))  # 没有指定就随机选一个
        if i > len(port_list):
            return ''
        return Http._VPN_URL + ':' + port_list[i - 1]

    @staticmethod
    def send_request_v(
            method: str,
            url: str,
            params: Union[Dict, str, None] = None,
            headers: Optional[Dict] = None,
            i = 0
    ) -> Union[Dict, str]:
        """
        发送HTTP请求并自动处理JSON响应
          - VPN模式，使用VPN - 可翻墙

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :param i: VPN 序号，不给就随机选一个
        :return: 如果响应是JSON则返回字典，否则返回原始文本
        """
        proxy = Http.get_vpn_url(i)
        return Http.send_request(method, url, params, headers, proxy)

    @staticmethod
    def get_mixed_rand():
        """获取混合模式下的随机值"""
        rand_list = Http._PROXY_RAND.split(',')
        return Attr.random_choice(rand_list)  # l, z, v, x

    @staticmethod
    def is_http_request():
        """
        判断当前是否处于 HTTP 请求上下文中
        :return: 如果是 HTTP 请求返回 True，否则返回 False
        """
        # return has_request_context()
        return Http.get_request_method() != 'COMMAND'

    @staticmethod
    def get_request_params():
        """获取请求参数 - GET + POST"""
        get_data = request.args.to_dict()
        if request.headers.get('Content-Type') == 'application/json':
            post_data = request.get_json()
        elif request.headers.get('Content-Type') == 'text/xml':
            post_data = {"xml": str(request.get_data(as_text=False).decode('utf-8'))}
        else:
            post_data = request.form.to_dict()
        get_data.update(post_data)
        return get_data

    @staticmethod
    def get_request_method():
        """
        获取当前 HTTP 请求的方式
        :return: 如果是 HTTP 请求的方式 GET | POST | COMMAND
        """
        try:
            # 尝试获取 Flask 请求的方法
            return request.method.upper()
        except RuntimeError:
            return 'COMMAND'

    @staticmethod
    def get_request_base_url(url):
        """获取请求的域名地址 - 含 http"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def get_request_route(strip=False):
        """获取除去域名和参数部分的请求路由地址"""
        if strip:
            return request.path.lstrip('/')
        return request.path

    @staticmethod
    def get_request_headers():
        """获取所有请求头 - 字典形式"""
        return json.loads(json.dumps(dict(request.headers), ensure_ascii=False, indent=4))

    @staticmethod
    def get_client_ip():
        """获取客户端真实的IP地址"""
        # 尝试从 X-Forwarded-For 头中获取客户端 IP 地址
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            # X-Forwarded-For 头可能包含多个 IP 地址，第一个是客户端的真实 IP 地址
            client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            # 如果没有 X-Forwarded-For 头，尝试从 X-Real-IP 头中获取客户端 IP 地址
            client_ip = request.headers.get('X-Real-IP')
        if not client_ip:
            # 如果仍然没有获取到客户端 IP 地址，使用 request.remote_addr
            client_ip = request.remote_addr
        return client_ip

    @staticmethod
    def replace_host(url: str, new_host: str) -> str:
        """
        替换URL中的域名部分

        :param url: 原始URL (e.g. "http://aa.bb.com:1011/bot/index.html?q=1")
        :param new_host: 新域名 (e.g. "cc.dd.cn")
        :return url: 替换后的URL (e.g. "http://cc.dd.cn:1011/bot/index.html?q=1")
        """
        # 使用正则表达式匹配并替换域名部分
        return re.sub(
            r'(https?://)[^/:]+(:[0-9]+)?(/|$)',
            lambda m: m.group(1) + new_host + (m.group(2) or '') + m.group(3),
            url,
            count=1  # 只替换第一个匹配项
        )

    @staticmethod
    def get_docker_inner_url(url):
        return Http.replace_host(url, 'host.docker.internal')


