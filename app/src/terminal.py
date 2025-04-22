import time
from datetime import datetime
from tool.router.base_app import BaseApp
from flask import render_template, stream_with_context, Response
from tool.core import *


class Terminal(BaseApp):

    def output(self):
        """#获取日志信息，前端页面展示用"""
        """实时日志页面展示"""
        if not self.params.get('key'):
            template = 'sys/terminal.html'
            return render_template(template)

        """实时日志输出流"""
        logger = Logger()
        # logger.debug("DEBUG TEST MSG")
        log_lock, log_queue = logger.get_log_queue()

        def generate():
            last_active = datetime.now()
            yield "retry: 300\n\n"
            for i in range(10):
                # 5分钟无客户端活动自动断开
                if (datetime.now() - last_active).total_seconds() > 300:
                    yield "event: timeout\ndata: 连接超时\n\n"
                if not log_queue.empty():
                    yield f"data: {log_queue.get()}\n\n"
                else:
                    break
            yield ":heartbeat\n\n"
            time.sleep(0.2)

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'X-Accel-Buffering': 'no',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )


