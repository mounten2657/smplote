import os
from pathlib import Path


class Dir:

    @staticmethod
    def root_dir():
        """获取项目根目录的绝对路径"""
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
    def static_dir(relative_path):
        """静态资源文件夹"""
        return Dir.abs_dir(f'storage/upload/static/{relative_path}')

    @staticmethod
    def exists(dir_path)->bool:
        """判断文件夹是否存在"""
        return os.path.exists(dir_path)

    @staticmethod
    def get_path_object(dir_path: str) -> Path:
        """获取路径对象"""
        path = Path(dir_path)
        if not path.is_dir() and not path.is_file():
            raise NotADirectoryError(f"'{dir_path}' 不是有效路径")
        return path

    @staticmethod
    def get_files_current(dir_path: str | Path) -> list[str]:
        """返回目录下的文件列表 - 仅当前目录 - 相对目录"""
        path = Dir.get_path_object(dir_path)
        return [f.name for f in path.iterdir() if f.is_file()]

    @staticmethod
    def get_files_recursive(dir_path: str | Path, file_only=1, exclude_dirs=None) -> list[str]:
        """返回目录下的文件列表 - 递归所有子目录 - 绝对目录"""
        path = Dir.get_path_object(dir_path)
        exclude_dirs = exclude_dirs or []  # 要排除的目录列表，如 ['.git', '.idea']
        return [str(p) for p in path.rglob("*") if not any(ex in p.parts for ex in exclude_dirs) and (not file_only or p.is_file())]

    @staticmethod
    def join_path(p1, p2)-> str:
        """路径合并"""
        return str(os.path.join(p1, p2))

