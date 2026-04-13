from tool.router.base_app import BaseApp
from service.source.preview.file_preview_service import FilePreviewService


class Raw(BaseApp):

    def enc(self):
        """encrypt file path"""
        return FilePreviewService.enc_path(self.params.get('path'))

    def image(self):
        """image preview"""
        return FilePreviewService.image(self.params.get('path'))

    def file(self):
        """office file preview"""
        return FilePreviewService.file(self.params.get('path'))

