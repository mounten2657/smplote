from typing import Callable
from vpp.proto.generated.vpp_serve_pb2 import *
from vpp.proto.generated.vpp_serve_pb2_grpc import *
from tool.core import Logger, Attr, Env, Ins, Str

logger = Logger()


@Ins.singleton
class VppServeClient:

    def __init__(self, host='', port=''):
        if not host or not port:
            host, port = self.get_vpp_config()
        self.channel = grpc.insecure_channel(
            f"{host}:{port}",
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024)
            ]
        )
        self.stub = VppServerStub(self.channel)

    @staticmethod
    def get_vpp_config():
        """获取默认配置"""
        host = Env.get('GRPC_HOST_VPP')
        port = Env.get('GRPC_PORT_VPP')
        return host, port

    def close(self):
        self.channel.close()

    @staticmethod
    def _exec_api(func: Callable, *args, **kwargs):
        """调用api接口"""
        response = func(*args, **kwargs)
        return {
            "code": response.code,"msg": response.msg,"data": Attr.parse_json_ignore(response.data)
        }

    def vp_download_file(self, fty, key, url, fp, fk, fd):
        """下载文件"""
        return self._exec_api(lambda: self.stub.vp_cdn_download(VpFileRequest(
            fty=fty, key=key, url=url,
            fp=fp, fk=fk, fd=fd
        )))

    def wk_html_2_img(self, fp, fo=''):
        """html转图片"""
        return self._exec_api(lambda: self.stub.wk_html_2_img(WkHtmlRequest(
            fp=fp, fo=fo
        )))

    def wk_html_2_pdf(self, fp, fo=''):
        """html转PDF"""
        return self._exec_api(lambda: self.stub.wk_html_2_pdf(WkHtmlRequest(
            fp=fp, fo=fo
        )))

    def cs7_http_req(self, m, u, p=None, h=None, x=None, t=None):
        """发送http请求"""
        p = Str.parse_json_string_ignore(p) if p else ''
        h = Str.parse_json_string_ignore(h) if h else ''
        t = int(t) if t else 0
        res = self._exec_api(lambda: self.stub.cs7_http(Cs7HttpRequest(m=m, u=u, p=p, h=h, x=x, t=t)))
        return res['data']
