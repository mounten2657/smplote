from tool.db.sqlite_db_handler import SqliteDBHandler
from tool.core import *


class WechatDBModule(SqliteDBHandler):

    def __init__(self, db_path: str = ''):
        self.db_path = db_path if db_path else Config.db_path()
        super().__init__(db_path)

    def get_room_name(self, g_wxid):
        """
        获取群聊名称
        :param g_wxid: 群聊的wxid
        :return:  群聊名称
        """
        info = (self.table('Session')
                .select(['strNickName'])
                .where({'strUsrName': g_wxid})
                .first())
        return info['strNickName'] if info else ''




