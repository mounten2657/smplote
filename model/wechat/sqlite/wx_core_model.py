from tool.db.sqlite_base_model import SqliteBaseModel
from tool.core import Ins


@Ins.singleton
class WxCoreModel(SqliteBaseModel):
    """微信本地核心数据库模型"""

    _table = None   # 不指定全库可查

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




