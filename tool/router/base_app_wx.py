from tool.router.base_app import BaseApp
from tool.core import Config


class BaseAppWx(BaseApp):

    _wx_config = None
    _wxid = None
    _wxid_dir = None
    _g_wxid = None
    _g_wxid_dir = None
    _g_name = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def wx_config(self):
        self._wx_config = self.get_wx_config()
        return self._wx_config

    @classmethod
    def get_wx_config(cls, account='a1', group='g1'):
        config = Config.wx_config()
        account = cls.get_params().get('ac', account)
        group = cls.get_params().get('gr', group)
        try:
            wx_config = {
                "account": config['account'][account],
                "group": config['group'][group]
            }
        except KeyError as e:
            raise RuntimeError(f'不存在的配置项：{e}')
        cls._wx_config = wx_config
        return cls._wx_config

    @property
    def wxid(self):
        wx_config = self.get_wx_config()
        self._wxid = wx_config['account']['wxid']
        return self._wxid

    @property
    def wxid_dir(self):
        wx_config = self.get_wx_config()
        self._wxid_dir = wx_config['account']['save_dir']
        return self._wxid_dir

    @property
    def g_wxid(self):
        wx_config = self.get_wx_config()
        self._g_wxid = wx_config['group']['wxid']
        return self._g_wxid

    @property
    def g_wxid_dir(self):
        wx_config = self.get_wx_config()
        self._g_wxid_dir = wx_config['group']['save_dir']
        return self._g_wxid_dir

    @property
    def g_name(self):
        wx_config = self.get_wx_config()
        self._g_name = wx_config['group']['name']
        return self._g_name
