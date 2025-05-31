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
