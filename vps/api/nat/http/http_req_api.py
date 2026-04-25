import requests
import subprocess
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
        :param int timeout: 超时时间，默认31秒
        :return: 返回json或文本
        """
        method = method.upper()
        params = Func.str_to_json(params) if params else {}
        headers = Func.str_to_json(headers) if headers else {}
        timeout = int(timeout) if timeout else 31

        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': timeout,
        }

        params_str = urlencode(params) if isinstance(params, dict) else params
        if 'GET' == method: request_kwargs.update({'params': params_str})
        elif 'JSON' == method: request_kwargs.update({'method': 'POST', 'json': params})
        elif 'PUT' == method: request_kwargs.update({'method': 'PUT', 'json': params})
        else: request_kwargs.update({'data': params_str})

        try:
            if not method.startswith('CURL'):
                rep = requests.request(**request_kwargs)
                rep.raise_for_status()
                if 'application/json' in rep.headers.get('Content-Type', ''):
                    return rep.json()
                rep = rep.text
            else:
                cmd_parts = "curl -s"
                headers = headers or {}
                for key, value in headers.items():
                    if key not in ['Cookie']:
                        cmd_parts += f' -H "{key}: {value}"'
                if params:
                    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                    if method.upper() == 'CURL_POST':
                        cmd_parts += f' -X POST -d "{str(param_str)}"'
                    else:
                        url = f"{url}&{param_str}" if "?" in url else f"{url}?{param_str}"
                cookie = headers.get('Cookie', '').strip()
                if cookie:
                    cmd_parts += f' -b "{cookie}"'
                curl_cmd = cmd_parts + f' "{str(url)}"'
                try:
                    rep = subprocess.check_output(curl_cmd, shell=True, timeout=timeout).decode('utf-8')
                except Exception as e:
                    err = str(e).replace(curl_cmd, '<curl>')
                    rep = f"curl failed: {err}"
            return Func.str_to_json(rep)
        except Exception as e:
            return f"HTTP request failed: {str(e)}"

