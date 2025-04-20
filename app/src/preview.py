from tool.router.base_app import BaseApp
from service.src.preview.file_preview import FilePreview


class Preview(BaseApp):

    def image(self):
        """image preview"""
        return FilePreview.image(self.params)

    def office(self):
        """office file preview"""
        return FilePreview.office(self.params)

