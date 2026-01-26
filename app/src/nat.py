from tool.router.base_app import BaseApp
from tool.core.http import Http


class Nat(BaseApp):

    def ppx(self):
        """利用代理池发起请求"""
        method = self.params.get('m', '')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        if not method or not url or not params:
            return self.error('Invalid params')
        return self.success(Http.send_request_x(method, url, params))

    def vpn(self):
        """利用vpn发起请求"""
        method = self.params.get('m', '')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        if not method or not url or not params:
            return self.error('Invalid params')
        return self.success(Http.send_request_v(method, url, params))
