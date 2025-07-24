import json
import requests
from urllib.parse import urlencode
from vps.base.func import Func


class HttpReqApi:

    def send_req(self, method, url, params=None, headers=None, timeout=None):
        """
        执行Http请求
        :param str method: 请求方式
        :param str url:  请求链接
        :param dict params: 请求参数
        :param dict headers: 请求头
        :param int timeout: 超时时间，默认30秒
        :return: 返回json或文本
        """
        method = method.upper()
        params = Func.str_to_json(params) if params else {}
        headers = Func.str_to_json(headers) if headers else {}
        timeout = int(timeout) if timeout else 30

        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': timeout,
        }

        params_str = urlencode(params) if isinstance(params, dict) else params
        if 'GET' == method:
            request_kwargs.update({'params': params_str})
        elif 'JSON' == method:
            request_kwargs.update({'method': 'POST', 'json': params})
        else:
            request_kwargs.update({'data': params_str})

        try:
            rep = requests.request(**request_kwargs)
            rep.raise_for_status()
            if 'application/json' in rep.headers.get('Content-Type', ''):
                return rep.json()
            return Func.str_to_json(rep.text)
        except Exception as e:
            msg = f"HTTP request failed: {str(e)}"
            print(msg)
            return msg

