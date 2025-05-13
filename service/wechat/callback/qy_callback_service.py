from utils.wechat.qywechat.callback.qy_callback_handler import QyCallbackHandler


class QyCallbackService:

    @staticmethod
    def callback_handler(app_key, params):
        return QyCallbackHandler().msg_handler(app_key, params)
