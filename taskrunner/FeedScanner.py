from twisted.internet.task import LoopingCall
from twisted.internet import reactor, threads
from twisted.internet.defer import inlineCallbacks, returnValue

from utils.SessionManager import SessionManager
from utils.DownloadManager import download_manager
from domain.Feed import Feed
from domain.Episode import Episode

import logging

logger = logging.getLogger(__name__)

class FeedScanner:
    '''
    This scanner will scan the 'feed' table with special interval. if any record has a field torrent_file_id is null.
    scanner will add this record to download application and get the torrent_file_id
    '''

    def __init__(self, base_path):
        self.interval = 30000
        self.base_path = base_path

    def start(self):
        lc = LoopingCall(self.scan_feed)
        lc.start(self.interval)

    def __query_feed(self):
        session = SessionManager.Session()
        try:
            return session.query(Feed).filter(Feed.torrent_file_id == None).all()
        finally:
            SessionManager.Session.remove()

    @inlineCallbacks
    def __update_episode(self, episode_id, torrent_file):
        session = SessionManager.Session()
        try:
            episode = session.query(Episode).filter(Episode.id == episode_id).one()
            if episode.torrent_files is not list:
                episode.torrent_files = []

            episode.torrent_files.append(torrent_file)

            episode.status = Episode.STATUS_DOWNLOADING
            session.commit()
            returnValue(None)
        finally:
            SessionManager.Session.remove()


    def __add_download(self, feed_list):
        for feed in feed_list:
            bangumi_path = self.base_path + '/' + str(feed.bangumi_id)
            torrent_file = yield download_manager.download(feed.download_url, bangumi_path)
            if torrent_file is None:
                logger.warn('episode %s download failed'.format(feed.episode_id))
            else:
                yield self.__update_episode(feed.episode_id, torrent_file)


    def __on_query_error(self, err):
        logger.warn(err)

    def scan_feed(self):
        d = threads.deferToThread(self.__query_feed)
        d.addCallback(self.__add_download)
        d.addErrback(self.__on_query_error)
