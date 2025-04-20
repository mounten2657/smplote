from tool.router.base_app import BaseApp
from tool.unit.img.md_to_img import MdToImg
from service.ai.report.ai_report_generator import AIReportGenerator


class DailyReport(BaseApp):

    def gen_report(self):
        """生成md总结"""
        res = AIReportGenerator.daily_report(self.g_wxid_dir, self.params)
        return self.success(res)

    def gen_md_img(self):
        """md 转图片"""
        res = MdToImg.gen_img(self.g_wxid_dir, self.params)
        return self.success(res)



