from tool.core import Config


class VpBaseFactory:

    app_key = None

    def __init__(self, app_key=None):
        self.app_key = app_key
        self.config = Config.vp_config()
        self.app_config = self.config['app_list'][self.app_key]
        self.self_wxid = self.app_config['wxid']
        self.a_g_wxid = self.app_config['g_wxid']

    def set_app_key(self, app_key):
        """切换账号"""
        self.app_key = app_key
        return self


