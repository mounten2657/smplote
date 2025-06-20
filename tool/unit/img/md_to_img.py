import os
from pathlib import Path
from tool.unit.html.md_to_html import MDToHtml
from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient
from tool.core import Api, Time, Dir, Emoji


class MdToImg:
    @staticmethod
    def gen_md_img(md_path, img_path=''):
        """
        将Markdown文件转换为图片
        :param md_path: MD文件路径，绝对路径
        :param img_path: 输出图片路径，相对路径
        :return 远程图片路径
        """
        img_path = img_path if img_path else Path(md_path).with_suffix('.png')
        if not os.path.exists(md_path):
            return Api.error(f'文件不存在： {md_path}')
        # 构建完整HTML
        html_path = MdToImg.gen_md_html(md_path)
        # 将html文件转为图片
        return VppServeClient().wk_html_2_img(str(html_path), str(img_path))

    @staticmethod
    def gen_md_html(md_path):
        md_obj = MDToHtml(md=md_path)
        html_path = Path(md_path).with_suffix('.html')
        full_html = Emoji.replace_emoji_to_img(md_obj.html)
        # full_html = md_obj.html
        md_obj.save_html(html_path, full_html)
        return html_path

    @staticmethod
    def gen_img(g_wxid_dir, params):
        # 默认今天
        start_time, end_time = Time.start_end_time_list(params)
        report_date = Time.dft(end_time if end_time else Time.now(), '%Y%m%d')
        g_name = os.path.basename(g_wxid_dir)
        res = [False] * 2
        md_file = f'{g_wxid_dir}/{report_date}/{g_name}_{report_date}.md'
        res[0] = MdToImg.gen_md_img(Dir.abs_dir(md_file))
        md_file = f'{g_wxid_dir}/{report_date}/{g_name}_{report_date}_detail.md'
        res[1] = MdToImg.gen_md_img(Dir.abs_dir(md_file))
        return res






