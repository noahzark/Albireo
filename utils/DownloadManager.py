from download_adapter import DelugeDownloader
from twisted.internet.defer import deferredGenerator, waitForDeferred


class DownloadManager:

    def __init__(self, downloader_cls):
        self.downloader = downloader_cls(self.on_download_completed)

    def on_download_completed(self):
        pass

    def download(self, magnet_uri, eps_no):
        def async_download():
            d = waitForDeferred(self.downloader.download(magnet_uri))
            yield d
            yield d.getResult()

        return deferredGenerator(async_download)

download_manager = DownloadManager(DelugeDownloader)