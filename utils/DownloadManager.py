from download_adapter.DelugeDownloader import DelugeDownloader
from twisted.internet.defer import deferredGenerator, waitForDeferred
from domain.bangumi_model import TorrentFile


class DownloadManager:

    def __init__(self, downloader_cls):
        self.downloader = downloader_cls(self.on_download_completed)

    def on_download_completed(self):
        pass

    def download(self, magnet_uri):
        return TorrentFile(torrent_id=0)

        # def async_download():
        #     d = waitForDeferred(self.downloader.download(magnet_uri))
        #     yield d
        #     yield d.getResult()

        # return deferredGenerator(async_download)

download_manager = DownloadManager(DelugeDownloader)