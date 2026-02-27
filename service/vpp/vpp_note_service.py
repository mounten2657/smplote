from tool.core import Logger, Dir, File
from utils.grpc.vpp_serve.vpp_serve_client import VppServeClient

logger = Logger()


class VppNoteService:

    @staticmethod
    def gen_note_html(note_path, output_dir):
        """
        生成 note 的 html

        :param note_path: 原始 markdown 笔记路径
        :param output_dir: 生成 html 笔记路径
        :return:
        """
        res = {}
        vpp_client = VppServeClient()
        if not note_path or not output_dir:
            return res | {'e': "Invalid params"}
        path = Dir.get_path_object(note_path)
        if path.is_dir():
            # 目录必须包含 note
            if '/note/' not in note_path:
                return res | {'e': "Note path not found"}
            f_list = Dir.get_files_recursive(note_path)
            if not f_list:
                return res | {'e': "File list not found"}
        else:
            return res | {'e': "Invalid path"}
        # 先清除旧文件夹
        Dir.delete_dir(output_dir)
        for f in f_list:
            ext = File.get_file_ext(f)
            # 路径转换 - 同级文件夹
            file_dir = File.get_file_dir(f)
            base_dir = Dir.join_path(output_dir, file_dir.split('/note/')[-1])
            if ext == 'md': # md 转 html
                res[f] = vpp_client.mdit_md_2_html(f, base_dir)
            elif '/zim/' in f:  # 图片直接复制过去
                if not Dir.exists(base_dir):
                    Dir.copy_dir(file_dir, base_dir)
        return res
