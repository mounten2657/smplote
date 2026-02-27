import json
from pathlib import Path


class Func:

    @staticmethod
    def str_to_json(s):
        """字符串转json"""
        try:
            return json.loads(s)
        except Exception as e:
            return s

    @staticmethod
    def get_files_cur(dir_path: str | Path) -> list[str]:
        """返回目录下的文件列表 - 仅当前目录 - 相对目录"""
        return [f.name for f in Path(dir_path).iterdir() if f.is_file()]

    @staticmethod
    def get_files_rec(dir_path: str | Path, file_only=1) -> list[str]:
        """返回目录下的文件列表 - 递归所有子目录 - 绝对目录"""
        return [str(p) for p in Path(dir_path).rglob("*") if not file_only or p.is_file()]


