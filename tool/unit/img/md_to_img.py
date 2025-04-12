import os
import imgkit
from imgkit.config import Config as MdConfig
from pathlib import Path
from tool.unit.html.md_to_html import MDToHtml
from tool.core import *


class MdToImg:
    @staticmethod
    def gen_md_img(md_path, img_path=''):
        """
        将Markdown文件转换为图片
        :param md_path: MD文件路径，相对路径
        :param img_path: 输出图片路径，相对路径
        """
        md_path = Dir.abs_dir(md_path)
        img_path = Dir.abs_dir(img_path) if img_path else Path(md_path).with_suffix('.png')
        if not os.path.exists(md_path):
            return Api.error(f'文件不存在： {md_path}')
        # 配置exe程序路径
        html_exe_path = r'E:\ai\orgs\tool\wkhtmlbox\wkhtmltopdf\bin\wkhtmltoimage.exe'
        config = MdConfig(wkhtmltoimage=html_exe_path)
        # 读取MD内容
        # md_content = libPath(Dir.abs_dir(md_path)).read_text(encoding='utf-8')
        # full_html = markdown.markdown(md_content)
        # 构建完整HTML
        full_html = MdToImg.gen_md_html(md_path)
        # 转换配置
        options = {
            'encoding': "UTF-8",
            # 'width': 800,
            'quality': 50,
            'enable-local-file-access': ""
        }
        # 转换为图片
        imgkit.from_string(full_html,img_path,options=options,config=config)
        return True

    @staticmethod
    def gen_md_html(md_path):
        md_obj = MDToHtml(md=md_path)
        html_path = Path(md_path).with_suffix('.html')
        full_html = Emoji.replace_emoji_to_img(md_obj.html)
        # full_html = md_obj.html
        md_obj.save_html(html_path, full_html)
        return full_html








