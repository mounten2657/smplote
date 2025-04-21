from tool.router.base_app import BaseApp
from flask import render_template, stream_with_context, Response
import time
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
            yield "retry: 300\n\n"
            for i in range(5):
                if not log_queue.empty():
                    yield f"data: {log_queue.get()}\n\n"
                else:
                    yield ":heartbeat\n\n"
                    break
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


