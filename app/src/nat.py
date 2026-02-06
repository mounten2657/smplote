from tool.router.base_app import BaseApp
from service.source.nat_service import NatService


class Nat(BaseApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nat = NatService()

    def ppr(self):
        """利用代理池发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.proxy_pool_request(method, url, params))

    def vpn(self):
        """利用vpn发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        o = self.params.get('o', '0')
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vpn_request(method, url, params, int(o)))

    def vps(self):
        """利用vps发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = self.params.get('p', '')
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vps_request(method, url, params))
