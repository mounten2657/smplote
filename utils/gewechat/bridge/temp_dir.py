import os
import pathlib


class TmpDir(object):
    """A temporary directory that is deleted when the object is destroyed."""

    tmpFilePath = pathlib.Path("./storage/tmp/")

    def __init__(self):
        path_exists = os.path.exists(self.tmpFilePath)
        if not path_exists:
            os.makedirs(self.tmpFilePath)

    def path(self):
        return str(self.tmpFilePath) + "/"
