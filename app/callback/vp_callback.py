from tool.router.base_app import BaseApp
from service.wechat.callback.vp_callback_service import VpCallbackService


class VpCallback(BaseApp):

    def collect_retry(self):
        """消息回放入口"""
        res = VpCallbackService.retry_handler(self.app_key, self.params)
        return self.success(res)

    def online_status(self):
        """获取在线状态"""
        res = VpCallbackService.online_status(self.app_key)
        return self.success(res)

    def start_ws(self):
        """启动 ws"""
        res = VpCallbackService.start_ws(self.app_key)
        return self.success(res)

    def close_ws(self):
        """关闭 ws"""
        res = VpCallbackService.close_ws(self.app_key)
        return self.success(res)
