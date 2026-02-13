from tool.core import Attr
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
        params = Attr.parse_json_ignore(self.params.get('p', ''))
        headers = Attr.parse_json_ignore(self.params.get('h', ''))
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.ppr_request(method, url, params, headers))

    def vpp(self):
        """利用vpp发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = Attr.parse_json_ignore(self.params.get('p', ''))
        headers = Attr.parse_json_ignore(self.params.get('h', ''))
        o = self.params.get('o', '0')
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vpp_request(method, url, params, headers, int(o)))

    def vps(self):
        """利用vps发起请求"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        headers = Attr.parse_json_ignore(self.params.get('h', ''))
        params = Attr.parse_json_ignore(self.params.get('p', ''))
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vps_request(method, url, params, headers))
