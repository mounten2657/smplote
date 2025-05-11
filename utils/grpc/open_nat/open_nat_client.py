from vps.base.desc import ConfigCrypto
from vps.proto.generated.open_nat_pb2 import *
from vps.proto.generated.open_nat_pb2_grpc import *
from tool.core import *

logger = Logger()


@Ins.singleton
class OpenNatClient:

    def __init__(self, host, port):
        self.channel = grpc.insecure_channel(
            f"{host}:{port}",
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024)
            ]
        )
        self.stub = OpenNatServiceStub(self.channel)

    def send_wechat_text(self, content, app_key, user_list=None):
        response = self.stub.SendWeChatText(WeChatTextRequest(
            content=content,
            app_key=app_key,
            user_list=user_list or ""
        ))
        return {
            "code": response.code,
            "msg": response.msg,
            "data": Attr.parse_json_ignore(response.data)
        }

    def close(self):
        self.channel.close()

    @staticmethod
    def init_config_qy():
        config = Config.qy_config()
        cryptor = ConfigCrypto(Env.get('APP_CONFIG_MASTER_KEY'))
        process = lambda d: {k: process(v) if isinstance(v, dict) else cryptor.encrypt(str(v)) for k, v in d.items()}
        File.save_file(process(config), Dir.abs_dir('vps/config/qy.json'))
        return True

    @staticmethod
    def send_text_msg(content, app_key='a1', host=Env.get('GRPC_HOST_ZGY'), port=Env.get('GRPC_PORT_ZGY')):
        """发送文本消息 - 对外方法"""
        client = OpenNatClient(host, port)
        return client.send_wechat_text(content, app_key)


