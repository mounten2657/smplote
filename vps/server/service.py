from concurrent import futures
import grpc
from vps.proto.open_nat_pb2 import *
from vps.proto.open_nat_pb2_grpc import *
from vps.api.wechat.qy_api.qy_msg_send import QYWeChatService
import os


class OpenNatService(OpenNatServiceServicer):

    def __init__(self):
        self.wechat_service = QYWeChatService(os.getenv('CONFIG_MASTER_KEY'))

    def SendWeChatText(self, request, context):
        try:
            result = self.wechat_service.send_text_message(
                content=request.content,
                app_key=request.app_key,
                user_list=request.user_list or None
            )
            return WeChatResponse(
                success=True,
                message="OK",
                data=str(result)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return WeChatResponse(
                success=False,
                message=str(e)
            )

    @staticmethod
    def serve():
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024)
            ]
        )
        add_OpenNatServiceServicer_to_server(OpenNatService(), server)
        server.add_insecure_port('[::]:30390')
        server.start()
        print("gRPC Server is running")
        server.wait_for_termination()
