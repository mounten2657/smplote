from tool.core import Http, Error, Logger, Str
from service.vps.open_nat_service import OpenNatService

logger = Logger()


class NatService:
    """网络请求分发类"""

    def proxy_pool_request(self, method, url, params, headers=None):
        """利用代理池发起请求"""
        return Http.send_request_x(method, url, params, headers)

    def vpn_request(self, method, url, params, headers=None):
        """利用vpn发起请求"""
        return Http.send_request_v(method, url, params, headers)

    def vps_request(self, method, url, params, headers=None):
        """利用vps发起请求"""
        return OpenNatService.send_http_request(method, url, params, headers)

    def mixed_request(self, method: str, url: str, params=None, headers=None, retry_times=3):
        """
        发送HTTP请求
          - 请求失败默认重试三次
          - 混合模式，各种模式随机请求
          - 此模式下每次发起请求的IP基本不会相同，适合于高频爬取网站数据

        :param method: HTTP方法 (GET/POST/PUT/DELETE等)
        :param url: 请求URL
        :param params: 查询参数，可以是字典或"a=1&b=2"格式字符串
        :param headers: 请求头字典
        :param retry_times: 失败的重试次数
        :return: json | str | err , r_type, proxy
        """
        res = {}
        proxy = ''
        r_type = Http.get_mixed_rand()
        uuid = Str.uuid()
        for i in range(0, retry_times):
            r_type = Http.get_mixed_rand() if i else r_type
            try:
                if r_type == 'x':  # 代理池 - 80%
                    proxy = Http.get_proxy(1)
                    res = Http.send_request(method, url, params, headers, proxy)
                elif r_type == 'v':  # VPN - 10%
                    proxy = Http.get_vpn_url()
                    res = Http.send_request(method, url, params, headers, proxy)
                elif r_type == 'z':   # VPS - 5%
                    proxy = 'vps'
                    res = self.vps_request(method, url, params, headers)
                else:  # 本地 - 5%
                    proxy = '_'
                    res = Http.send_request(method, url, params, headers)
            except Exception as e:
                err = Error.handle_exception_info(e)
                logger.warning(f"请求失败<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_WAR')
                if i == retry_times - 1:
                    logger.error(f"请求错误，已超过最大重试次数<{uuid}><{r_type}>[{i + 1}/{retry_times}][{proxy}]: {url} - {params} - {err}", 'MIXED_ERR')
                    return err, r_type, proxy
        return res, r_type, proxy

