import threading
from tool.core import *
from tool.router import *
from typing import Dict, Any, Optional


class BaseApp:

    _instance: Optional['BaseApp'] = None  # 单例模式，避免重复实例化
    _instance_lock = threading.Lock()           # 保证多线程环境下单例的唯一性，避免竞态条件
    _logger = None
    _db_config = None
    _wx_config = None
    _wxid = None
    _wxid_dir = None
    _g_wxid = None
    _g_wxid_dir = None
    _g_name = None

    def __new__(cls, **kwargs):
        with cls._instance_lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance.__init__(**kwargs)
        return cls._instance

    def __init__(self, **kwargs):
        self.args = kwargs
        self.root_dir = Dir.root_dir()
        self.params = self.get_params()

    def __reduce__(self):
        return self.__class__, ()

    @classmethod
    def get_params(cls) -> Dict[str, Any]:
        if not Http.is_http_request():
            return ParseHandler.get_command_params()
        return RouterHandler.get_http_params()

    @property
    def logger(self):
        if not self._logger:
            self._logger = Logger()
        return self._logger

    @property
    def db_config(self, db_name='default'):
        self._db_config = Config.db_config(db_name)
        return self._db_config

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

    @classmethod
    def success(cls, data=None, msg='success', code=0):
        return Api.success(data, msg, code)

    @classmethod
    def error(cls, msg='error', data=None, code=999):
        return Api.error(msg, data, code)



