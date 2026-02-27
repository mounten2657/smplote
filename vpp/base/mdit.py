import re
from pathlib import Path
from typing import List, Dict
from string import Template
from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.footnote import footnote_plugin


class Mdit:
    """MD 转 HTML 类"""

    # HTML 模板
    BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>$title</title>
    <link rel="icon" href="/favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="/theme/md/omh.css">
</head>
<body class="dark-theme">
    <div class="app-container">
        <div class="sidebar">
            <h2>
                <a href="/">目录</a>
                <a href="../">↿↾ PRE</a>
                <span class="right-group">
                    <a class="theme-toggle" href="#" id="themeToggle">☀️</a>
                    <a class="theme-toggle" href="$s_url" target="_self">$s_name</a>
                </span>
            </h2>
            <ul class="toc-list">
                $toc_html
            </ul>
        </div>
        <div class="content">
            <h1 id="file-title">$file_title</h1>
            $content_html
        </div>
    </div>
    <script src="/theme/md/highlight.min.js"></script>
    <script src="/theme/md/highlight-line-numbers.min.js"></script>
    <script src="/theme/md/omh.js"></script>
</body>
</html>
    """

    def __init__(self, md_path: str, output_dir: str = "./output"):
        """
        初始化转换器
        :param md_path: Markdown文件路径
        :param output_dir: HTML输出目录
        """
        self.is_share = '/share/' in md_path
        self.md_path = Path(md_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 读取MD内容
        with open(self.md_path, 'r', encoding='utf-8') as f:
            self.raw_md_content = f.read()

        # 预处理MD内容，修复linkify和strikethrough问题
        self.md_content = self._preprocess_md_content(self.raw_md_content)

        # 解析后的标题（用于生成目录）
        self.headings: List[Dict[str, str | int]] = []
        # 文件名作为一级标题
        self.file_title = self.md_path.stem

        # 初始化markdown-it-py解析器（按你的优化调整）
        self.md_parser = self._init_md_parser()

    def _init_md_parser(self) -> MarkdownIt:
        """初始化markdown-it-py解析器，仅启用核心扩展"""
        # 创建解析器实例，启用所有常用功能
        md = (
            MarkdownIt("commonmark", {"linkify": True})
            .enable("table")  # 启用表格支持
            .enable("strikethrough")  # 启用删除线
            .enable("linkify")  # 启用自动链接识别（核心功能）
            .use(front_matter_plugin)  # 支持front matter
            .use(footnote_plugin)  # 脚注插件
        )

        # 配置代码块语言前缀，保持和之前一致
        md.options["langPrefix"] = "language-"

        return md

    def _preprocess_md_content(self, content: str) -> str:
        """
        预处理Markdown内容，修复两个核心问题：
          - 链接间丢失换行符问题
          - 删除线包裹链接不生效问题
        """
        # 匹配连续的链接行（每行都是纯链接），确保换行符保留
        # 正则匹配：以链接开头结尾的行，在行尾添加换行标记
        link_line_pattern = re.compile(
            r'^(https?://[^\s]+)(\n|$)',
            re.MULTILINE | re.IGNORECASE
        )
        content = link_line_pattern.sub(r'\1<br>\r\n', content)

        # 匹配 ~~链接~~ 格式，在链接后添加空格（避免解析冲突）
        strikethrough_link_pattern = re.compile(
            r'~~\s*(https?://[^\s]+)\s*~~',
            re.IGNORECASE
        )
        # 替换为 ~~<链接>~~（修复删除线）
        content = strikethrough_link_pattern.sub(r'~~<\1>~~', content)

        return content

    def _extract_headings(self) -> None:
        """提取Markdown中的标题，生成目录数据"""
        # 逐行解析标题，兼容markdown-it-py的解析规则
        heading_pattern = re.compile(r'^(#{1,5})\s+(.*)$', re.MULTILINE)
        matches = heading_pattern.findall(self.raw_md_content)  # 使用原始内容解析标题

        self.headings = []
        # 记录重复ID，避免冲突
        id_counter = {}

        for level_str, text in matches:
            level = len(level_str)
            text_clean = text.strip()
            # 生成唯一ID：保留字母/数字/空格，空格替换为-，其他替换为_
            heading_id = re.sub(r'[^\w\s]', '_', text_clean).replace(' ', '-').lower()

            # 处理重复ID
            if heading_id in id_counter:
                id_counter[heading_id] += 1
                heading_id = f"{heading_id}_{id_counter[heading_id]}"
            else:
                id_counter[heading_id] = 0

            self.headings.append({
                'level': level,
                'text': text_clean,
                'id': heading_id
            })

    def _generate_toc_html(self) -> str:
        """生成目录的HTML（包含文件名标题）"""
        # 先添加文件名作为一级目录
        toc_html = f'<li><a href="#file-title" class="toc-level-1">{self.file_title}</a></li>'

        # 添加MD中的标题
        for heading in self.headings:
            level = heading['level']
            text = heading['text']
            heading_id = heading['id']
            toc_html += (
                f'<li><a href="#{heading_id}" class="toc-level-{level}">'
                f'{text}</a></li>'
            )
        return toc_html

    def _add_heading_ids(self, html_content: str) -> str:
        """给HTML中的标题添加正确的ID"""
        # 遍历所有标题，精准替换
        for heading in self.headings:
            level = heading['level']
            text = heading['text']
            heading_id = heading['id']

            # 更精准的匹配：不依赖原有ID，直接匹配标题文本
            pattern = re.compile(
                f'(<h{level}>\\s*)({re.escape(text)})(\\s*</h{level}>)',
                re.IGNORECASE | re.DOTALL
            )
            replacement = f'\\1<span id="{heading_id}"></span>\\2\\3'

            if not pattern.search(html_content):
                pattern = re.compile(
                    f'(<h{level}>.*?)({re.escape(text)})(.*?</h{level}>)',
                    re.IGNORECASE | re.DOTALL
                )
                replacement = f'\\1<span id="{heading_id}"></span>\\2\\3'

            html_content = pattern.sub(replacement, html_content)

        return html_content

    def convert(self) -> str:
        """执行转换，返回HTML内容并保存文件"""
        # 提取标题（使用原始MD内容）
        self._extract_headings()

        # 使用markdown-it-py转换预处理后的Markdown到HTML
        content_html = self.md_parser.render(self.md_content)

        # 修复标题ID
        content_html = self._add_heading_ids(content_html)

        # 生成目录HTML
        toc_html = self._generate_toc_html()

        # 登出 or 置顶
        s_url = '/?_dc=1' if not self.is_share else '#file-title'
        s_name = '登出' if not self.is_share else '置顶'

        # 替换模板变量
        title = self.file_title
        template = Template(self.BASE_TEMPLATE)
        final_html = template.substitute(
            title=title,
            toc_html=toc_html,
            file_title=self.file_title,
            content_html=content_html,
            s_url=s_url,
            s_name=s_name,
        )

        # 保存文件
        output_file = self.output_dir / f"{self.md_path.stem}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_html)

        #print(f"转换完成！HTML文件已保存到: {output_file}")
        return final_html
