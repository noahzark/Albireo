from Downloader import Downloader
from yaml import load
from deluge.ui.client import client
from twisted.internet.defer import inlineCallbacks, returnValue
# Set up the logger to print out errors
from deluge.log import setupLogger, LOG
setupLogger(level='info')


class DelugeDownloader(Downloader):

    def __init__(self, on_download_completed_callback):

        fr = open('./config/config.yml', 'r')
        config = load(fr)
        self.delugeConfig = config['deluge']

        self.__on_download_completed_callback = on_download_completed_callback

    def __on_connect_success(self, result):
        '''
        : add event handlers
        '''
        LOG.info('Connection was successful')
        client.register_event_handler('TorrentFinishedEvent', self.__on_download_completed)
        return result

    def __on_connect_fail(self, result):
        '''
        :throw a exception
        '''
        raise Exception()

    def connect_to_daemon(self):
        deferred = client.connect(**self.delugeConfig)

        deferred.addCallback(self.__on_connect_success)
        deferred.addErrback(self.__on_connect_fail)

        return deferred

    def __on_download_completed(self, torrent_id):
        self.__on_download_completed_callback(torrent_id)

    @inlineCallbacks
    def download(self, magnet_uri, download_location):
        torrent_id = yield client.core.add_torrent_magnet(magnet_uri, {'download_location': download_location})
        # if move_done_path is not None:
        #     result = yield client.core.set_torrent_move_completed_path(torrent_id, move_done_path)
        #     print(result)
        returnValue(torrent_id)