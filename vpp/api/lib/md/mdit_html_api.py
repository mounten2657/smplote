from vpp.base.mdit import Mdit


class MditHtmlApi:
    """MD 转 HTML """

    @staticmethod
    def md2html(m, o):
        """
        markdown 转 html

        :param m: md 文件路径
        :param o: 输出文件夹，生成文件名相同的 html 文件
        :return: 操作结果
        """
        res = {}
        if not m or not o:
            return res | {'e': "Invalid params"}
        # md 转 html:
        res['md'] = Mdit(md_path=m, output_dir=o).convert()
        return res

