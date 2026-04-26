from tool.core import Attr
from tool.router.base_app import BaseApp
from service.source.nat_service import NatService


class Nat(BaseApp):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nat = NatService()

    def _get_nat_params(self):
        """获取请求参数"""
        method = self.params.get('m', 'GET')
        url = self.params.get('u', '')
        params = Attr.parse_json_ignore(self.params.get('p', ''))
        headers = Attr.parse_json_ignore(self.params.get('h', ''))
        o = self.params.get('o') if self.params.get('o') else '0'
        return method, url, params, headers, o

    def ppr(self):
        """利用代理池发起请求"""
        method, url, params, headers, o = self._get_nat_params()
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.ppr_request(method, url, params, headers))

    def vpp(self):
        """利用vpp发起请求"""
        method, url, params, headers, o = self._get_nat_params()
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vpp_request(method, url, params, headers, int(o)))

    def vps(self):
        """利用vps发起请求"""
        method, url, params, headers, o = self._get_nat_params()
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vps_request(method, url, params, headers))

    def vpr(self):
        """利用vps代理池发起请求"""
        method, url, params, headers, o = self._get_nat_params()
        if not url:
            return self.error('Invalid url')
        return self.success(self.nat.vpr_request(method, url, params, headers))

