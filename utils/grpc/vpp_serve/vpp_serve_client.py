from vpp.proto.generated.vpp_serve_pb2 import *
from vpp.proto.generated.vpp_serve_pb2_grpc import *
from tool.core import Logger, Attr, Env, Ins

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

    def vp_download_file(self, fty, key, url, fp, fk, fd):
        response = self.stub.vp_cdn_download(VpFileRequest(
            fty=fty,
            key=key,
            url=url,
            fp=fp,
            fk=fk,
            fd=fd
        ))
        return {
            "code": response.code,
            "msg": response.msg,
            "data": Attr.parse_json_ignore(response.data)
        }

    @staticmethod
    def download_file(fty, key, url, fp, fk, fd=0):
        """
        下载文件 - 对外方法
        :param int fty: 文件类型
        :param str key: 加密密钥
        :param str url: 加密url
        :param str fp: 文件保存路径
        :param str fk: 假名 - 需唯一
        :param int fd: 是否强制下载,，默认否
        :return: 可访问的文件链接 、文件md5 以及 文件大小
        """
        return VppServeClient().vp_download_file(fty, key, url, fp, fk, fd)
