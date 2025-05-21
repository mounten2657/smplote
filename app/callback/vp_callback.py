from tool.router.base_app import BaseApp
from service.wechat.callback.vp_callback_service import VpCallbackService


class VpCallback(BaseApp):

    def online_status(self):
        """获取在线状态"""
        app_key = self.params.get('app_key', 'a1')
        res = VpCallbackService.online_status(app_key)
        return self.success(res)


