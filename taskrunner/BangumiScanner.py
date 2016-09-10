from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.Feed import Feed
from datetime import datetime
from sqlalchemy.sql import func
import logging
import random
from twisted.internet import threads

logger = logging.getLogger(__name__)


class BangumiScanner:
    def __init__(self, base_path):
        self.base_path = base_path

    def __find_episode_by_number(self, episode_list, eps_no):
        for episode in episode_list:
            if episode.episode_no == eps_no:
                return episode
        return None

    def download_episodes(self, url_eps_id_list, bangumi_id):
        session = SessionManager.Session()
        try:
            for (download_url, episode_id) in url_eps_id_list:
                feed = Feed(download_url = download_url,
                            episode_id = episode_id,
                            bangumi_id = bangumi_id)
                session.add(feed)
            session.commit()
        except Exception as error:
            logger.warn(error)

        finally:
            SessionManager.Session.remove()


    def check_bangumi_status(self, bangumi):
        return bangumi.status == Bangumi.STATUS_FINISHED

    def update_bangumi_on_air(self, bangumi):
        if bangumi.air_date <= datetime.today().date():
            bangumi.status = Bangumi.STATUS_ON_AIR

    def update_bangumi_status(self, bangumi):
        session = SessionManager.Session
        try:
        # if bangumi has no not downloaded episode, we consider it's finished.
            episode_count = session.query(func.count(Episode.id)). \
                filter(Episode.bangumi == bangumi). \
                filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED). \
                scalar()

            if (bangumi.status == Bangumi.STATUS_ON_AIR) and (episode_count == 0):
                bangumi.status = Bangumi.STATUS_FINISHED
            session.commit()
        except Exception as error:
            logger.warn(error)
        finally:
            SessionManager.Session.remove()

    def query_bangumi_list(self):
        session = SessionManager.Session()
        try:
            return session.query(Bangumi).\
                filter(Bangumi.status != Bangumi.STATUS_FINISHED).\
                filter(Bangumi.rss != None).all()
        except Exception as error:
            logger.warn(error)
            return []
        finally:
            SessionManager.Session.remove()

    def query_episode_list(self, bangumi_id):
        session = SessionManager.Session()
        try:
            return session.query(Episode). \
                filter(Episode.bangumi_id == bangumi_id). \
                filter(Episode.status == Episode.STATUS_NOT_DOWNLOADED). \
                all()
        except Exception as error:
            logger.warn(error)
            return []
        finally:
            SessionManager.Session.remove()

    def has_keyword(self, bangumi):
        '''
        subclass should override this method
        :param bangumi:
        :return: {boolean}
        '''
        return False

    def scan_feed(self,bangumi, episode_list):
        '''
        subclass should override this method
        :param bangumi,
        :param episode_list
        :return: list of tuples (download_url, episode_no)
        '''
        return []

    def scan_bangumi(self):
        '''
        dispatch the feed crawling job, this is a synchronized method running on individual thread
        :return:
        '''
        bangumi_list = yield threads.deferToThread(self.query_bangumi_list, self)

        for index in random.shuffle(range(len(bangumi_list))):
            bangumi = bangumi_list[index]
            if self.has_keyword(bangumi) and (not self.check_bangumi_status(bangumi)):
                episode_list = yield threads.deferToThread(self.query_episode_list, self, bangumi.id)
                # result is an array of tuple (item, eps_no)
                scan_result = yield threads.deferToThread(self.scan_feed, self, bangumi, episode_list)
                url_eps_id_list = [(download_url, self.__find_episode_by_number(episode_list, eps_no)) for (download_url, eps_no) in scan_result]
                # this method may raise exception
                yield threads.deferToThread(self.download_episodes, self, url_eps_id_list, bangumi.id)
                self.update_bangumi_status(bangumi)
