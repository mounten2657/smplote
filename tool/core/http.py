import json
import requests
import re
from urllib.parse import urlencode
from typing import Union, Dict, Optional
from flask import request, has_request_context
from tool.core.attr import Attr


class Http:

    @staticmethod
    def send_request(
            method: str,
            url: str,
            params: Union[Dict, str, None] = None,
            headers: Optional[Dict] = None
    ) -> Union[Dict, str]:
        """
        发送HTTP请求并自动处理JSON响应
        Args:
            method: HTTP方法 (GET/POST/PUT/DELETE等)
            url: 请求URL
            params: 查询参数，可以是字典或"a=1&b=2"格式字符串
            headers: 请求头字典
        Returns:
            如果响应是JSON则返回字典，否则返回原始文本
        Raises:
            ValueError: 方法不支持或参数无效
            requests.exceptions.RequestException: 请求失败
        """
        # 参数校验
        method = method.upper()
        if method not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'):
            raise ValueError(f"Unsupported HTTP method: {method}")

        # 处理params参数
        params_str = None
        if isinstance(params, dict):
            params_str = urlencode(params)
        elif isinstance(params, str):
            params_str = params if '=' in params else None

        # 发送请求
        try:
            rep = requests.request(
                method=method,
                url=url,
                params=params_str,
                headers=headers or {},
                timeout=10
            )
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
        Args:
            url: 原始URL (e.g. "http://aa.bb.com:1011/bot/index.html?q=1")
            new_host: 新域名 (e.g. "cc.dd.cn")
        Returns:
            url: 替换后的URL (e.g. "http://cc.dd.cn:1011/bot/index.html?q=1")
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


