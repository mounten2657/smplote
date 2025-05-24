import websocket
from threading import Thread
import time
from tool.core import Logger, Attr, Ins, Config

logger = Logger()


@Ins.singleton
class VpSocketFactory:
    def __init__(self, uri, handler, app_key):
        self.ws = None
        self.uri = uri
        self.handler = handler
        self.app_key = app_key
        self.config = Config.vp_config()
        self.app_config = self.config['app_list'][self.app_key]
        self.thread = None
        self.is_running = False
        self._stop_event = False

    def _handler_exec(self, method, ext=None):
        """所有方法交由回调器处理"""
        handler = self.handler + f'.{method}'
        action, ins = Attr.get_action_by_path(handler, 1, self.app_key)
        if action:
            try:
                logger.debug(f"[{self.app_key}]已发送至回调: {handler}", "VP_HD_STA")
                res = action(ext)
                res and logger.info(f"[{self.app_key}]回调处理结果: {res}", "VP_HD_RES")
                return True
            except Exception as e:
                logger.error(f"[{self.app_key}]回调处理失败: {e}", "VP_HD_ERR")
        return False

    def _on_message(self, ws, message):
        if any(key in message for key in str(self.app_config['g_wxid_exc']).split(',')):
            return False  # 无用的消息日志都不需要打印
        message = Attr.parse_json_ignore(message)  # 尝试转json
        contents = str(message.get('content', {}).get('str', '')).replace('\n', ' ')[:32]
        m_type = message.get('msg_type', 0)
        logger.debug(f"[{self.app_key}]收到消息[T{m_type}]: {contents}", "VP_REV")
        self._handler_exec('on_message', {"message": message})

    def _on_error(self, ws, error):
        logger.error(f"[{self.app_key}]连接错误: {error}", "VP_ERR")
        self._handler_exec('on_error', {"message": error})

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info(f"[{self.app_key}]连接关闭: {close_status_code} {close_msg}", "VP_CLD")
        self.is_running = False
        self._handler_exec('on_close', {"message": close_msg, "code": close_status_code})

    def _on_open(self, ws):
        logger.info(f"[{self.app_key}]连接已建立 - {self.uri}", "VP_OPE")
        self.is_running = True
        self._handler_exec('on_open', {})

    def _connect(self):
        while not self._stop_event:
            if not self.is_running:
                time.sleep(1)  # 连接前等待
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
                    logger.error(f"[{self.app_key}]连接异常: {e}", "VP_ERR")
                    time.sleep(5)  # 重连前等待

    def start(self):
        """启动 WebSocket 连接"""
        if not self.thread or not self.thread.is_alive():
            self._stop_event = False
            self.thread = Thread(target=self._connect, daemon=True)
            self.thread.start()
            logger.info(f"[{self.app_key}]正在启动 WebSocket 连接...", "VP_STA")
        else:
            logger.warning(f"[{self.app_key}]WebSocket 已启动，无需重复操作", "VP_STA")
        return True

    def close(self):
        """安全关闭 WebSocket 连接"""
        if self.is_running and self.ws:
            logger.info(f"[{self.app_key}]正在关闭 WebSocket 连接...", "VP_CST")
            self._stop_event = True
            self.is_running = False
            self.ws.close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=2.0)
            self.ws = None
            logger.info(f"[{self.app_key}]WebSocket 连接已关闭", "VP_CED")
        else:
            logger.warning(f"[{self.app_key}]WebSocket 已关闭，无需重复操作", "VP_CED")
        return True

    def __del__(self):
        self.close()
