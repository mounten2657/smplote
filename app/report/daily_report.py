import os
from tool.router.base_app import BaseApp
from tool.unit.txt.replace_name import ReplaceName
from tool.unit.img.md_to_img import MdToImg
from tool.unit.ai.ai_report_generator import AIReportGenerator


class DailyReport(BaseApp):

    def gen_report(self):
        """生成md总结"""
        res = AIReportGenerator.daily_report(self.g_wxid_dir, self.params)
        return self.success(res)

    def gen_md_img(self):
        """md 转图片"""
        res = MdToImg.gen_img(self.g_wxid_dir, self.params)
        return self.success(res)

    def replace_name(self):
        """替换人名测试"""
        replacement_dict = {
            "微信用户名1": "🍒群备注1",
            "微信用户名2": "🥑群备注2"
        }
        input_file = 'data/file/group/g1/20250404/test.txt'
        res = ReplaceName.replace_names(input_file, replacement_dict)
        return self.success(res)



