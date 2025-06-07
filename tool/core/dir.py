import os


class Dir:
    @staticmethod
    def root_dir():
        """
        获取项目根目录的绝对路径。
        该方法通过获取当前文件（dir.py）的绝对路径，然后逐级向上查找，直到找到包含 tool 文件夹的目录，即为项目根目录。
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        while True:
            parent_dir = os.path.dirname(current_dir)
            if os.path.basename(parent_dir) == 'tool':
                return os.path.dirname(parent_dir)
            current_dir = parent_dir

    @staticmethod
    def abs_dir(relative_path):
        """
        将传入的相对路径转换为相对于项目根目录的绝对路径。
        :param relative_path: 相对于项目根目录的相对路径
        :return: 转换后的绝对路径
        """
        project_root = Dir.root_dir()
        full_path = os.path.join(project_root, relative_path)
        # 根据系统类型统一斜杠
        if os.sep == '\\':  # Windows 系统
            full_path = full_path.replace('/', '\\')
        else:  # Linux 或 macOS 系统
            full_path = full_path.replace('\\', '/')
        return full_path

    @staticmethod
    def wechat_dir(relative_path):
        """微信文件夹"""
        return Dir.abs_dir(f'storage/upload/wechat/{relative_path}')
