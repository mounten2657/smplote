import os
from pathlib import Path


class WkHtmlApi:
    """wk插件"""

    @staticmethod
    def wk_html_to_img(fp, fo=''):
        """html 转 图片"""
        out_file = ''
        fo = fo if fo else Path(fp).with_suffix('.png')
        if 0 == os.system(f'/usr/bin/xvfb-run /usr/bin/wkhtmltoimage --quality 80 --format png {fp} {fo}'):
            out_file = fo
        return {"lp": out_file}

    @staticmethod
    def wk_html_to_pdf(fp, fo=''):
        """html 转 PDF"""
        out_file = ''
        fo = fo if fo else Path(fp).with_suffix('.pdf')
        if 0 == os.system(f'/usr/bin/xvfb-run /usr/bin/wkhtmltopdf {fp} {fo}'):
            out_file = fo
        return {"lp": out_file}
