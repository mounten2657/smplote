from tool.router.base_app import BaseApp
from tool.core import Config, Attr
from utils.wechat.vpwechat.vp_client import VpClient


class BaseAppVp(BaseApp):

    _vp_config = None
    _app_config = None
    _wxid = None
    _wxid_name = None
    _g_wxid = None
    _g_name = None
    _g_wxid_list = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def vp_config(self):
        self._vp_config = Config.vp_config()
        return self._vp_config

    @property
    def app_config(self):
        self._app_config = self.vp_config['app_list'][self.app_key]
        return self._app_config

    @property
    def wxid(self):
        self._wxid = self.app_config['wxid']
        return self._wxid

    @property
    def wxid_name(self):
        client = VpClient(self.app_key)
        room = client.get_room(self.g_wxid)
        user = Attr.select_item_by_where(room.get('member_list', []), {"wxid": self.wxid})
        self._wxid_name = user.get('display_name', '')
        return self._wxid_name

    @property
    def g_wxid(self):
        self._g_wxid = str(self.app_config['g_wxid']).split(',')[0]
        return self._g_wxid

    @property
    def g_name(self):
        client = VpClient(self.app_key)
        room = client.get_room(self.g_wxid)
        self._g_name = room.get('nickname', '')
        return self._g_name

    @property
    def g_wxid_list(self):
        self._g_wxid_list = self.app_config['g_wxid']
        return self._g_wxid_list
