import datetime
from tool.router.base_app import BaseApp
from tool.unit.txt.replace_name import ReplaceName
from tool.unit.img.md_to_img import MdToImg


class DailySummary(BaseApp):

    def replace_name(self):
        # 替换人名
        replacement_dict = {
            "微信用户名1": "🍒群备注1",
            "微信用户名2": "🥑群备注2"
        }
        input_file = 'data/file/group/g1/20250404/test.txt'
        res = ReplaceName.replace_names(input_file, replacement_dict)
        return self.success(res)

    def md_img(self):
        date = datetime.datetime.now().strftime('%Y%m%d')
        md_file = f'data/file/group/g1/{date}/g1_{date}_1d.md'
        res = MdToImg.gen_md_img(md_file)
        return self.success(res)
