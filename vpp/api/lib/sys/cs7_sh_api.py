import os
import requests
from urllib.parse import urlencode
from vpp.base.func import Func


class Cs7ShApi:
    """centos7 shell """

    @staticmethod
    def restart_gunicorn(p):
        """重启gunicorn"""
        sh = os.system(f'sudo /opt/shell/init/init_flask.sh >>/tmp/init_flask.log 2>&1')
        return {"p": p, "sh": sh}

    @staticmethod
    def send_cs7_http(m, u, p=None, h=None, x=None, t=None):
        """
        执行Http请求 - 支持代理

        :param str m: 请求方式
        :param str u:  请求链接
        :param dict p: 请求参数
        :param dict h: 请求头
        :param str x: 代理地址，默认空
        :param int t: 超时时间，默认30秒
        :return: 返回json或文本
        """
        m = m.upper()
        p = Func.str_to_json(p) if p else {}
        h = Func.str_to_json(h) if h else {}
        t = int(t) if t else 30

        request_kwargs = {'method': m, 'url': u, 'headers': h, 'timeout': t}
        if x: request_kwargs['proxies'] = {'http': x, 'https': x}

        params_str = urlencode(p) if isinstance(p, dict) else p
        if 'JSON' == m: request_kwargs.update({'method': 'POST', 'json': p})
        elif 'PUT' == m: request_kwargs.update({'method': 'PUT', 'json': p})
        elif 'GET' == m: request_kwargs.update({'params': params_str})
        else: request_kwargs.update({'data': params_str})

        try:
            rep = requests.request(**request_kwargs)
            rep.raise_for_status()
            if 'application/json' in rep.headers.get('Content-Type', ''):
                return rep.json()
            return Func.str_to_json(rep.text)
        except Exception as e:
            return f"HTTP request failed: {str(e)}"

