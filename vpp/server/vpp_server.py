import os
import json
import signal
from concurrent import futures
from typing import Callable
from vpp.proto.generated.vpp_serve_pb2 import *
from vpp.proto.generated.vpp_serve_pb2_grpc import *
from vpp.api.wechat.pad.vp_file_api import VpFileApi
from vpp.api.lib.wk.wk_html_api import WkHtmlApi
from vpp.api.lib.sys.cs7_sh_api import Cs7ShApi


class VppServer:

    def __init__(self):
        self.file_api = VpFileApi()
        self.wk_api = WkHtmlApi()
        self.cs7_api = Cs7ShApi()

    def vp_cdn_download(self, request, context):
        """下载文件"""
        return self._exec_api(context, lambda: self.file_api.download_file(
                fty=request.fty, key=request.key, url=request.url,
                fp=request.fp, fk=request.fk, fd=request.fd,
        ))

    def wk_html_2_img(self, request, context):
        """转图片"""
        return self._exec_api(context, lambda: self.wk_api.wk_html_to_img(
                fp=request.fp, fo=request.fo
        ))

    def wk_html_2_pdf(self, request, context):
        """转PDF"""
        return self._exec_api(context, lambda: self.wk_api.wk_html_to_pdf(
                fp=request.fp, fo=request.fo
        ))

    def cs7_rgu(self, request, context):
        """重启gunicorn"""
        return self._exec_api(context, lambda: self.cs7_api.restart_gunicorn(p=request.p))

    @staticmethod
    def _exec_api(context, func: Callable, *args, **kwargs):
        """执行api方法"""
        try:
            result = func(*args, **kwargs)
            result = result if result else {}
            return CommonResponse(
                code=int(result.get('code', 0)),msg=result.get('msg', 'success'),data=json.dumps(result)
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            return CommonResponse(code=9999,msg=str(e),data='Null')

    @staticmethod
    def _shutdown_handler(server):
        """注册信号处理"""
        def signal_handler(sig, frame):
            pid = os.getpid()
            print(f"\n[{pid}] - 接收到关闭信号，正在关闭服务...")
            server.stop(3).wait()  # 给服务器时间处理现有请求
            print(f"[{pid}] - 服务已停止")
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # 系统终止信号

    @staticmethod
    def run():
        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10),
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),
                ('grpc.max_receive_message_length', 100 * 1024 * 1024)
            ]
        )
        add_VppServerServicer_to_server(VppServer(), server)
        with open('config/vp.json', 'r', encoding='utf-8') as f:
            config = json.loads(f.read().strip())
        server.add_insecure_port(config['grpc_url'])
        server.start()
        print("gRPC Server is running")
        try:
            VppServer._shutdown_handler(server)
            server.wait_for_termination()
        except KeyboardInterrupt:
            pass
