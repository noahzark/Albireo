from Downloader import Downloader
from yaml import load
from deluge.ui.client import client


class DelugeDownloader(Downloader):

    def __init__(self, on_download_completed_callback):

        fr = open('../config/config.yml', 'r')
        config = load(fr)
        self.delugeConfig = config['deluge']

        self.__on_download_completed_callback = on_download_completed_callback

        self.__connect_to_daemon()

    def __on_connect_success(self):
        '''
        : add event handlers
        '''
        client.register_event_handler('TorrentFileFinished', self.__on_download_completed)

    def __on_connect_fail(self):
        '''
        :throw a exception
        '''
        raise Exception()

    def __connect_to_daemon(self):
        deferred = client.connect(**self.delugeConfig)

        deferred.addCallback(self.__on_connect_success)
        deferred.addErrback(self.__on_connect_fail)

    def __on_download_completed(self, torrent_id):
        self.__on_download_completed_callback(torrent_id)

    def download(self, magnet_uri):
        return client.core.add_torrent_magnet(magnet_uri)
