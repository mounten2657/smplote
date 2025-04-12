import os
from tool.router.base_app import BaseApp
from tool.unit.txt.replace_name import ReplaceName
from tool.unit.img.md_to_img import MdToImg
from tool.unit.ai.ai_report_generator import AIReportGenerator
from tool.core import *


class DailyReport(BaseApp):

    def gen_report(self):
        """生成md总结"""
        start_time, end_time = Time.start_end_time_list(self.params)
        report_date = Time.dft(end_time if end_time else Time.now(), '%Y%m%d')
        res = AIReportGenerator.daily_report(self.g_wxid_dir, report_date)
        return self.success(res)

    def gen_md_img(self):
        """md 转图片"""
        start_time, end_time = Time.start_end_time_list(self.params)
        report_date = Time.dft(end_time if end_time else Time.now(), '%Y%m%d')
        g_name = os.path.basename(self.g_wxid_dir)
        md_file = f'{self.g_wxid_dir}/{report_date}/{g_name}_{report_date}.md'
        res = MdToImg.gen_md_img(md_file)
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



