import os
import json
from concurrent import futures
from vps.proto.generated.open_nat_pb2 import *
from vps.proto.generated.open_nat_pb2_grpc import *
from vps.api.wechat.qy.qy_msg_api import QYMsgApi


class OpenNatServer(OpenNatServerServicer):

    def __init__(self):
        self.msg_api = QYMsgApi(os.getenv('APP_CONFIG_MASTER_KEY'))

    def SendWeChatText(self, request, context):
        try:
            result = self.msg_api.send_text_message(
                content=request.content,
                app_key=request.app_key,
                user_list=request.user_list or None
            )
            result = result if result else {}
            return CommonResponse(
                code=int(result.get('errcode', 0)),
                msg=result.get('errormsg', 'success'),
                data=json.dumps(result)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return CommonResponse(
                code=9999,
                msg=str(e),
                data='Null',
            )

    @staticmethod
    def run():
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024)
            ]
        )
        add_OpenNatServerServicer_to_server(OpenNatServer(), server)
        server.add_insecure_port('0.0.0.0:30390')
        server.start()
        print("gRPC Server is running")
        server.wait_for_termination()
