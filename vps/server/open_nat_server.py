import os
import json
from concurrent import futures
from vps.proto.generated.open_nat_pb2 import *
from vps.proto.generated.open_nat_pb2_grpc import *
from vps.api.wechat.qy.qy_msg_api import QYMsgApi
from vps.api.nat.http.http_req_api import HttpReqApi


class OpenNatServer(OpenNatServerServicer):
    """
    Vps 服务类
      - pip install mypy-protobuf
      - pip install --upgrade protobuf
      - rm -rf ./vps/proto/generated/*
      - python -m grpc_tools.protoc -I./vps/proto --python_out=./vps/proto/generated --grpc_python_out=./vps/proto/generated --mypy_out=./vps/proto/generated ./vps/proto/open_nat.proto
      - vps/proto/generated/open_nat_pb2_grpc.py:6
      - import vps.proto.generated.open_nat_pb2 as open__nat__pb2
      - python -m vps.server.app &
    """

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
            return CommonResponse(code=9999, msg=str(e), data='Null')

    def NatHttpSend(self, request, context):
        try:
            result = HttpReqApi().send_req(
                method=request.method,
                url=request.url,
                params=request.params or None,
                headers=request.headers or None,
                timeout=request.timeout or None
            )
            result = result if result else {}
            return CommonResponse(code=0, msg='success', data=json.dumps(result))
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return CommonResponse(code=9998, msg=str(e), data='Null')

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
