from tool.router.base_app import BaseApp
from service.source.preview.file_preview_service import FilePreviewService


class Preview(BaseApp):

    def image(self):
        """image preview"""
        return FilePreviewService.image(self.params)

    def office(self):
        """office file preview"""
        return FilePreviewService.office(self.params)

