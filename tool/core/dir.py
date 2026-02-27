import os
import shutil
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
    def wechat_dir(relative_path):
        """微信文件夹"""
        return Dir.abs_dir(f'storage/upload/wechat/{relative_path}')

    @staticmethod
    def exists(dir_path)->bool:
        """判断文件夹是否存在"""
        return os.path.exists(dir_path)

    @staticmethod
    def mkdir(dir_path)->None:
        """创建文件夹"""
        return os.makedirs(dir_path, exist_ok=True)

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
    def get_files_recursive(dir_path: str | Path, file_only=1) -> list[str]:
        """返回目录下的文件列表 - 递归所有子目录 - 绝对目录"""
        path = Dir.get_path_object(dir_path)
        return [str(p) for p in path.rglob("*") if not file_only or p.is_file()]

    @staticmethod
    def join_path(p1, p2)-> str:
        """路径合并"""
        return str(os.path.join(p1, p2))

    @staticmethod
    def copy_dir(src: str | Path, dst: str | Path, ignore_patterns=None) -> None:
        """
        复制整个文件夹（包括所有子目录和文件）

        :param src: 源文件夹路径
        :param dst: 目标文件夹路径（如果不存在会自动创建）
        :param ignore_patterns: 可选，忽略的文件模式列表，例如 ['*.tmp', '__pycache__']
        :return: None
        """
        src = Path(src).resolve()
        dst = Path(dst).resolve()
        if not src.is_dir():
            raise NotADirectoryError(f"源路径不是目录: {src}")
        if dst.exists():  # 如果目标已存在，先删除
            shutil.rmtree(dst)
        if ignore_patterns:
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*ignore_patterns))
        else:
            shutil.copytree(src, dst)

    @staticmethod
    def delete_dir(path: str | Path, ignore_errors=False) -> None:
        """
        删除整个文件夹（包括所有内容）

        :param path: 要删除的文件夹路径
        :param ignore_errors: 是否忽略删除错误（默认False，建议生产环境设为True）
        :return: None
        """
        path = Path(path).resolve()
        if not path.exists():  # 已不存在，直接返回
            return
        if not path.is_dir():
            raise NotADirectoryError(f"不是目录: {path}")
        shutil.rmtree(path, ignore_errors=ignore_errors)

