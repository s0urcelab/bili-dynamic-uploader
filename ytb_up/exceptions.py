from .constants import *

class YoutubeUploadError(Exception):
    def __init__(self, message, code=YTB_ERR_DEFAULT):
        self.message = message
        self.code = code

    def __str__(self):
        return self.message
