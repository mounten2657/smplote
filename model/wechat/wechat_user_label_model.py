from tool.db.mysql_base_model import MysqlBaseModel
from tool.core import Ins


@Ins.singleton
class WechatUserLabelModel(MysqlBaseModel):
    """
    微信用户标签表
        - id - int - 主键ID
        - wxid - varchar(32) - 用户微信ID
        - l_id - int - 标签ID
        - l_name - varchar(64) - 标签名称
        - create_at - datetime - 记录创建时间
        - update_at - datetime - 记录更新时间
    """

    _table = 'wechat_user_label'

    def add_label(self, label, wxid):
        """数据入库"""
        # 先删除再入库
        self.delete({"wxid": wxid})
        insert_list = []
        for lab in label:
            insert_list.append({
                "wxid": wxid,
                "l_id": lab['labelId'],
                "l_name": lab['labelName'],
            })
        return self.insert(insert_list)

    def get_label(self, wxid):
        """获取用户标签列表"""
        return self.select(["l_id as id", "l_name as name"]).where({"wxid": wxid}).get()
