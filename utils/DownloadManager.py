from twisted.internet.defer import inlineCallbacks, returnValue

from download_adapter.DelugeDownloader import DelugeDownloader
from domain.bangumi_model import TorrentFile


class DownloadManager:

    def __init__(self, downloader_cls):
        self.downloader = downloader_cls(self.on_download_completed)

    def connect(self):
        '''
        connect to a downloader daemon, currently use deluge.
        :return: a Deferred object
        '''
        return self.downloader.connect_to_daemon()

    def on_download_completed(self, torrent_id):
        print 'Download complete'
        print 'torrent_id %s' % torrent_id
        def get_files(files):
            print files
        d = self.downloader.get_files(torrent_id)
        d.addCallback(get_files)

    @inlineCallbacks
    def download(self, magnet_uri, move_done_path):
        torrent_id = yield self.downloader.download(magnet_uri, move_done_path)
        returnValue(TorrentFile(torrent_id=torrent_id))

download_manager = DownloadManager(DelugeDownloader)
