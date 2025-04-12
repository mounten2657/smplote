import requests
from flask import has_request_context


class Http:
    @staticmethod
    def send_http_request(method, url, headers=None, params=None, data=None, json=None):
        """
        发起 HTTP 请求的通用方法
        :param method: 请求方法，如 'GET' 或 'POST'
        :param url: 请求的 URL
        :param headers: 请求头，字典类型
        :param params: GET 请求的参数，字典类型
        :param data: POST 请求的表单数据，字典类型
        :param json: POST 请求的 JSON 数据，字典类型
        :return: 响应对象
        """
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=data, json=json)
            else:
                raise ValueError(f"不支持的请求方法: {method}")
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"请求出错: {e}")
            return None

    @staticmethod
    def is_http_request():
        """
        判断当前是否处于 HTTP 请求上下文中
        :return: 如果是 HTTP 请求返回 True，否则返回 False
        """
        return has_request_context()

