from twisted.internet.task import LoopingCall
from twisted.internet import reactor, threads
from twisted.internet.defer import inlineCallbacks, returnValue

from utils.SessionManager import SessionManager
from utils.DownloadManager import download_manager
from domain.Feed import Feed
from domain.Episode import Episode
from domain.VideoFile import VideoFile
from domain.WatchProgress import WatchProgress
from domain.Favorites import Favorites

import logging

logger = logging.getLogger(__name__)

class FeedScanner:
    '''
    This scanner will scan the 'feed' table with special interval. if any record has a field torrent_file_id is null.
    scanner will add this record to download application and get the torrent_file_id
    '''

    def __init__(self, base_path):
        self.interval = 30
        self.base_path = base_path

    def start(self):
        lc = LoopingCall(self.scan_feed)
        lc.start(self.interval)

    def __query_video_file(self):
        session = SessionManager.Session()
        try:
            return session.query(VideoFile).\
                filter(VideoFile.download_url != None).\
                filter(VideoFile.status == VideoFile.STATUS_DOWNLOAD_PENDING).\
                all()
        finally:
            SessionManager.Session.remove()

    def __update_video_file(self, video_file_list, torrent_id):
        session = SessionManager.Session()
        try:
            for video_file in video_file_list:
                session.add(video_file)
                video_file.torrent_id = torrent_id
                video_file.status = VideoFile.STATUS_DOWNLOADING
            session.commit()
        finally:
            SessionManager.Session.remove()

    @inlineCallbacks
    def __add_download(self, video_file_list):
        logger.debug(video_file_list)
        download_url_dict = {}
        for video_file in video_file_list:
            if video_file.download_url not in download_url_dict:
                download_url_dict[video_file.download_url] = []
            download_url_dict[video_file.download_url].append(video_file)

        for download_url, same_torrent_video_file_list in download_url_dict.iteritems():
            first_video_file = same_torrent_video_file_list[0]
            bangumi_path = self.base_path + '/' + str(first_video_file.bangumi_id)
            try:
                torrent_id = yield download_manager.download(first_video_file.download_url, bangumi_path)
                logger.info(torrent_id)
                if torrent_id is None:
                    logger.warn('episode %s already in download queue', str(first_video_file.episode_id))
                else:
                    yield threads.deferToThread(self.__update_video_file, same_torrent_video_file_list, torrent_id)
            except Exception as error:
                logger.warn(error)
                logger.warn('episode %s download failed', str(first_video_file.episode_id))


    def __on_query_error(self, err):
        logger.warn(err)

    def scan_feed(self):
        logger.info('scan feed')
        d = threads.deferToThread(self.__query_video_file)
        d.addCallback(self.__add_download)
        d.addErrback(self.__on_query_error)
