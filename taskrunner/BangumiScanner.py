from utils.SessionManager import SessionManager
from utils.DownloadManager import download_manager
from utils.CountDownLatch import CountDownLatch
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from feed.DMHY import DMHY
from feed.ACG_RIP import ACG_RIP
from datetime import datetime
from sqlalchemy.sql import func
from twisted.internet import reactor, threads
from twisted.internet.defer import inlineCallbacks, returnValue
import logging
import errno
import os
import yaml
import random
import threading

logger = logging.getLogger(__name__)


class BangumiScanner:
    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.interval = int(config['task']['interval']) * 60
        self.base_path = config['download']['location']
        self.feedparser = config['feedparser']

        self.bangumi_feed_item = {}

        self.count_down_latch = CountDownLatch(2)
        self.lock = threading.Lock()

        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
                logger.info('create base dir %s successfully', self.base_path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                logger.error(exception)

    def __find_episode_by_number(self, episode_list, eps_no):
        for episode in episode_list:
            if episode.episode_no == eps_no:
                return episode
        return None

    def __download_callback(self, nothing):
        pass


    @inlineCallbacks
    def __add_to_download(self, download_url, episode, bangumi):
        '''
        add current episode to download, when download is added, update episode status and add torrent_file record
        :param item: the item of corresponding episode, it contains an enclosure list which has magnet uri
        :param eps_no: the episode number
        :return: the episode number, the return value is useless
        '''
        bangumi_path = self.base_path + '/' + str(bangumi.id)
        torrent_file = yield threads.blockingCallFromThread(reactor, download_manager.download, download_url, bangumi_path)
        if torrent_file is None:
            logger.warn('episode %s of %s added failed'.format(episode.episode_no, bangumi.name))
            returnValue(None)
        else:

            if episode.torrent_files is not list:
                episode.torrent_files = []

            episode.torrent_files.append(torrent_file)

            episode.status = Episode.STATUS_DOWNLOADING
            logger.info('episode %s of %s added', episode.episode_no, bangumi.name)
            returnValue(None)

    def download_episodes(self, items, episode_list, bangumi):
        with self.lock:
            bangumi_id = str(bangumi.id)
            if bangumi_id not in self.bangumi_feed_item:
                    self.bangumi_feed_item[bangumi_id] = {}
            for item in items:
                if item[0] is None:
                    logger.warn('missing url in episode %s of bangumi %s'.format((str(item[1]), bangumi.name)))
                    continue
                episode = self.__find_episode_by_number(episode_list, item[1])
                episode_id = str(episode.id)
                if episode is None:
                    logger.warn('missing episode of %s in bangumi %s'.format((item[1], bangumi.name)))
                    continue
                if episode_id not in self.bangumi_feed_item[bangumi_id]:
                    self.bangumi_feed_item[bangumi_id][episode_id] = True
                    d = self.__add_to_download(item[0], episode, bangumi)
                    d.addCallback(self.__download_callback)


    def check_bangumi_status(self, bangumi):
        with self.lock:
            return bangumi.status == Bangumi.STATUS_FINISHED

    def update_bangumi_on_air(self, bangumi):
        with self.lock:
            if bangumi.air_date <= datetime.today().date():
                bangumi.status = Bangumi.STATUS_ON_AIR

    def update_bangumi_status(self, bangumi):
        with self.lock:
            session = SessionManager.Session
            # if bangumi has no not downloaded episode, we consider it's finished.
            episode_count = session.query(func.count(Episode.id)). \
                filter(Episode.bangumi == bangumi). \
                filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED). \
                scalar()

            if (bangumi.status == Bangumi.STATUS_ON_AIR) and (episode_count == 0):
                bangumi.status = Bangumi.STATUS_FINISHED

    def dispatch_feed(self, bangumi_list, feed_crawler_cls):
        '''
        dispatch the feed crawling job, this is a synchronized method running on individual thread
        :param bangumi_list:
        :param feed_crawler:
        :return:
        '''
        try:
            session = SessionManager.Session
            for index in random.shuffle(range(len(bangumi_list))):
                bangumi = bangumi_list[index]
                if feed_crawler_cls.has_keyword(bangumi) and (not self.check_bangumi_status(bangumi)):
                    episode_result = session.query(Episode). \
                        filter(Episode.bangumi == bangumi). \
                        filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED)
                    feed_crawler = feed_crawler_cls(bangumi, episode_result)
                    # result is an array of tuple (item, eps_no)
                    # this method may raise exception
                    self.download_episodes(feed_crawler.parse_feed(), episode_result, bangumi)
                    self.update_bangumi_status(bangumi)
        except Exception as error:
            logger.warn(error)
        finally:
            self.count_down_latch.count_down()

    def _scan_bangumi_in_thread(self):
        logger.debug('start scan bangumi')

        session = SessionManager.Session

        bangumi_list = session.query(Bangumi). \
            filter(Bangumi.status != Bangumi.STATUS_FINISHED). \
            filter(Bangumi.keywords != None). \
            all()

        # DMHY
        dmhy_thread = threading.Thread(target=self.dispatch_feed, args=(self, bangumi_list, DMHY))
        dmhy_thread.daemon = True
        dmhy_thread.start()

        # acg.rip
        acg_rip_thread = threading.Thread(target=self.dispatch_feed, args=(self, bangumi_list, ACG_RIP))
        acg_rip_thread.daemon = True
        acg_rip_thread.start()

        # nyaa has no torrent or magnet url in feed item. so we cannot support nyaa currently
        # nyaa_thread = threading.Thread(target=self.dispatch_feed, args=(self, bangumi_list, NYAA))
        # nyaa_thread.daemon = True
        # nyaa_thread.start()

        self.count_down_latch.await()

        session.commit()

        # try:
        #     for bangumi in result:
        #         # update status
        #         if bangumi.air_date <= datetime.today().date():
        #             bangumi.status = Bangumi.STATUS_ON_AIR
        #
        #         episode_result = session.query(Episode). \
        #             filter(Episode.bangumi == bangumi). \
        #             filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED)
        #
        #         http_proxy = self._get_proxy(bangumi.rss)
        #
        #         task = DMHY(bangumi, episode_result, self.base_path, http_proxy)
        #
        #         if 'timeout' in self.feedparser:
        #             timeout = int(self.feedparser['timeout'])
        #         else:
        #             timeout = None
        #
        #         task_result = task.parse_feed(timeout)
        #         if task_result is None:
        #
        #             # if bangumi has no not downloaded episode, we consider it's finished.
        #             episode_count = session.query(func.count(Episode.id)). \
        #                 filter(Episode.bangumi == bangumi). \
        #                 filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED). \
        #                 scalar()
        #
        #             if (bangumi.status == Bangumi.STATUS_ON_AIR) and (episode_count == 0):
        #                 bangumi.status = Bangumi.STATUS_FINISHED
        #
        #             session.commit()
        #             logger.debug('scan finished')
        #         else:
        #             logger.warn('scan %s finished with exception', bangumi.id)
        #             logger.warn(task_result)
        #
        #
        # except OSError as os_error:
        #     logger.error(os_error)
        # except exc.DBAPIError as db_error:
        #     logger.error(db_error)
        #     # if connection is invalid rollback the session
        #     if db_error.connection_invalidated:
        #         session.rollback()
        # except Exception as error:
        #     logger.error(error)
        #     traceback.print_exc()
