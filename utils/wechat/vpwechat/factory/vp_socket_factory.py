import websocket
from threading import Thread
import time
from tool.core import Logger, Attr

logger = Logger()


class VpSocketFactory:
    def __init__(self, uri, handler, app_key):
        self.ws = None
        self.uri = uri
        self.handler = handler
        self.app_key = app_key
        self.thread = None
        self.is_running = False
        self.start()

    def _handler_exec(self, method, ext=None):
        """所有方法交由回调器处理"""
        handler = self.handler + f'.{method}'
        action = Attr.get_action_by_path(handler, self.app_key)
        if action:
            try:
                logger.debug(f"已发送至回调: {handler}", "VP_HD_STA")
                res = action(ext)
                logger.info(f"回调处理结果: {res}", "VP_HD_RES")
            except Exception as e:
                logger.error(f"回调处理失败: {e}", "VP_HD_ERR")

    def _on_message(self, ws, message):
        message = Attr.parse_json_ignore(message)  # 尝试转json
        contents = str(message.get('content', {}).get('str', '')).replace('\n', ' ')[:64]
        m_type = message.get('msg_type', 0)
        logger.debug(f"收到消息[T{m_type}]: {contents}", "VP_REV")
        self._handler_exec('on_message', {"message": message})

    def _on_error(self, ws, error):
        logger.error(f"连接错误: {error}", "VP_ERR")
        self._handler_exec('on_error', {"message": error})

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"连接关闭: {close_status_code} {close_msg}", "VP_CLD")
        self.is_running = False
        self._handler_exec('on_close', {"message": close_msg, "code": close_status_code})

    def _on_open(self, ws):
        logger.info("连接已建立", "VP_OPE")
        self.is_running = True
        self._handler_exec('on_open', {})

    def _connect(self):
        while not self.is_running:  # 处理重连
            time.sleep(5)  # 连接前等待
            try:
                self.ws = websocket.WebSocketApp(
                    self.uri,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self.ws.run_forever()
            except Exception as e:
                logger.error(f"连接异常: {e}", "VP_ERR")
                time.sleep(5)  # 重连前等待

    def start(self):
        """启动 WebSocket 连接"""
        if not self.thread or not self.thread.is_alive():
            self.thread = Thread(target=self._connect, daemon=True)
            self.thread.start()
            logger.info("正在启动 WebSocket 连接...", "VP_STA")

    def send(self, message):
        """发送消息（带重连机制）"""
        if not self.is_running:
            logger.warning("连接未建立，尝试重新连接", "VP_TRY")
            self.start()
            time.sleep(1)  # 等待连接建立

        if self.is_running and self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(message)
                return True
            except Exception as e:
                logger.error(f"发送消息失败: {e}", "VP_ERR")
                self.is_running = False
        return False

    def close(self):
        """安全关闭 WebSocket 连接"""
        if self.is_running and self.ws:
            logger.info("正在关闭 WebSocket 连接...", "VP_CST")
            self.is_running = False
            self.ws.close()

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)

            self.ws = None
            logger.info("WebSocket 连接已关闭", "VP_CED")


