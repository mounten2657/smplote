import re
import json
import requests
import random
import itertools
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
    _XQ_URL = Env.get('PROXY_API_URL_XQ')
    _XQ_UID = Env.get('PROXY_API_UID_XQ')
    _XQ_KEY = Env.get('PROXY_API_KEY_XQ')

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

        # 初始化请求参数
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers or {},
            'timeout': 30,
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
        res['ip'] = str(Http.send_request('GET', url, headers=headers, proxy='')).strip()
        if not res['ip']:
            return Api.error(f"Get local ip failed: {url}")
        url = f"{Http._XQ_OPT_URL}/IpWhiteList.aspx"
        params = {
            "uid": Http._XQ_OPT_UID,
            "ukey": Http._XQ_OPT_KEY,
        }
        res['get'] = Http.send_request('GET', url, params | {"act": "getjson"})  # {"data":[{"IP":"x.x.x.x","MEMO":""}]}
        if not res['get']:
            return Api.error(f"Get white ip failed: {res['get']}")
        wip = Attr.get_by_point(res["get"], 'data.0.IP')
        if not wip or wip == res["ip"]:
            return res
        res['del'] = Http.send_request('GET', url, params | {"act": "del", "ip": "all"})  # success
        if not res['del']:
            return Api.error(f"Get white ip failed: {res['del']}")
        res['add'] = Http.send_request('GET', url, params | {"act": "add", "ip": res['ip']})  # success
        if not res['add']:
            return Api.error(f"Get white ip failed: {res['add']}")
        return res

    @staticmethod
    def get_proxy_tunnel(pn=None):
        """
        随机获取代理隧道池编号

        :param int pn: 隧道池编号
        :return: 隧道号
        """
        if pn is not None:
            return int(pn)
        # {隧道池编号: 数量} - 确保数量多的隧道被选中的概率最高
        number_counts = {
            51: 75,  # J池 （50%）
            82: 18,  # D池
            57: 18,  # B池
            61: 18,  # Z池
            62: 12,  # X池
            76: 9  # X池 （三分钟版）
        }
        number_list = list(itertools.chain.from_iterable(
            [num] * count for num, count in number_counts.items()
        ))
        return random.choice(number_list)

    @staticmethod
    def get_proxy(pn=None):
        """
        获取代理ip

        :param int pn: 隧道池编号
        :return: 代理ip 和 端口  + 获取结果
        """
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
            "num": 1
        }
        res = Http.send_request('GET', url, params)  # {"code":0,"success":"true","msg":"","data":[{"IP":"x.x.x.x","Port":5639,"IpAddress":"Unknow"}]}
        ip = Attr.get_by_point(res, 'data.0.IP')
        port = Attr.get_by_point(res, 'data.0.Port')
        if not ip or not port:
            return res, False
        return f"http://{ip}:{port}", True

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
        proxy, pf = Http.get_proxy()
        if not pf:
            return Api.error(f"Get http proxy failed: {proxy}")
        return Http.send_request(method, url, params, headers, proxy)

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


