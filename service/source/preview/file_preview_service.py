import os
from flask import send_from_directory, abort
from pathlib import Path
from tool.core import *


class FilePreviewService:

    BASE_STORAGE_DIR = Dir.abs_dir('storage/upload')
    ALLOW_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    ALLOW_FILE_EXT = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', 'mp4', 'mp3'}

    @staticmethod
    def image(file_path):
        """图片预览"""
        file_path, full_path = FilePreviewService._check_path(file_path)

        # 检查文件类型（仅允许图片）
        allowed_extensions = FilePreviewService.ALLOW_IMAGE_EXT
        if Path(file_path).suffix.lower() not in allowed_extensions:
            abort(415, description="Unsupported media type")

        # 发送文件
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        return send_from_directory(directory, filename)

    @staticmethod
    def office(file_path):
        """office文件预览"""
        file_path, full_path = FilePreviewService._check_path(file_path)

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in FilePreviewService.ALLOW_FILE_EXT:
            abort(415, description="不支持的文件类型")

        # 返回文件下载（浏览器会尝试预览）
        return send_from_directory(
            os.path.join(FilePreviewService.BASE_STORAGE_DIR, os.path.dirname(file_path)),
            os.path.basename(file_path),
            as_attachment=False  # False允许浏览器尝试预览
        )

    @staticmethod
    def _check_path(file_path):
        if not file_path:
            abort(400, description="Missing path parameter")

        # 安全检查
        if not File.is_safe_path(FilePreviewService.BASE_STORAGE_DIR, file_path):
            abort(403, description="Access denied")

        # 检查文件是否存在
        full_path = os.path.join(FilePreviewService.BASE_STORAGE_DIR, file_path)
        if not os.path.isfile(full_path):
            abort(404, description="File not found")

        return file_path, full_path




