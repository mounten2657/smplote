from tool.router.base_app import BaseApp
from tool.core.http import Http


class Nat(BaseApp):

    def ppr(self):
        """利用代理池发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        if not url:
            return self.error('Invalid url')
        return self.success(Http.send_request_x(method, url, params))

    def vpn(self):
        """利用vpn发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        if not url:
            return self.error('Invalid url')
        return self.success(Http.send_request_v(method, url, params))
