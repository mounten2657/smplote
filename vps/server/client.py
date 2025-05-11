import grpc
from vps.proto.open_nat_pb2 import *
from vps.proto.open_nat_pb2_grpc import *

class OpenNatClient:
    def __init__(self, host='localhost', port=50051):
        self.channel = grpc.insecure_channel(
            f"{host}:{port}",
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024)
            ]
        )
        self.stub = OpenNatServiceStub(self.channel)

    def send_wechat_text(self, content, app_key="a1", user_list=None):
        response = self.stub.SendWeChatText(WeChatTextRequest(
            content=content,
            app_key=app_key,
            user_list=user_list or ""
        ))
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data
        }


# 使用示例
if __name__ == '__main__':
    client = OpenNatClient('hba2.wch1.top', 30390)
    result = client.send_wechat_text("测试gRPC消息")
    print(result)
