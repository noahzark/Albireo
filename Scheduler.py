import logging
import os, errno

FORMAT = '%(asctime)-15s %(module)s:%(lineno)d %(message)s'

logging.basicConfig(format=FORMAT, datefmt='%Y/%m/%d %H:%M:%S')

logger = logging.getLogger()

isDebug = os.getenv('DEBUG', False)

if isDebug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


import platform
if platform.system() == 'Linux':
    from twisted.internet import epollreactor
    epollreactor.install()
else:
    from twisted.internet import selectreactor
    selectreactor.install()

from twisted.internet import reactor, threads


from feed_scanner.DMHY import DMHY
from yaml import load
from utils.SessionManager import SessionManager
from utils.VideoManager import video_manager
from domain.Episode import Episode
from domain.Bangumi import Bangumi
from twisted.internet.task import LoopingCall
from utils.DownloadManager import download_manager
from utils.exceptions import SchedulerError
from urlparse import urlparse
from sqlalchemy import exc
from sqlalchemy.sql import func
from datetime import datetime
import traceback

from taskrunner.InfoScanner import info_scanner


class Scheduler:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = load(fr)
        self.interval = int(config['task']['interval']) * 60
        self.base_path = config['download']['location']
        self.feedparser = config['feedparser']
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

    def start(self):
        lc = LoopingCall(self.scan_bangumi)
        lc.start(self.interval)

    def get_url_name(self, url):
        '''
        get the site name by given url
        :param url:
        :return: the site name if not found return default
        '''
        url_name_map = {
            'share.dmhy.org': 'dmhy',
            'share.dmhy.net': 'dmhy',
            'bangumi.moe': 'bangumi',
        }
        location = urlparse(url)[1]

        if location in url_name_map:
            return url_name_map[location]
        else:
            return 'default'

    def _get_proxy(self, rss_url):
        '''
        get the proxy config from config and given url,
        if url specific config is not found using the default config.
        if config is an string, treat it as proxy url, use it for all three schemes
        if config is an dict, make sure it has all scheme set and use it directly
        :param rss_url:
        :return: an dict of config
        '''
        if 'proxy' in self.feedparser:
            proxy_config = self.feedparser['proxy']
            url_name = self.get_url_name(rss_url)
            # find config by name, if not found, use default, if default is not set, return None
            if url_name in proxy_config:
                proxy_for_name = proxy_config[url_name]
            elif 'default' in proxy_config:
                proxy_for_name = proxy_config['default']
            else:
                return None

            if type(proxy_for_name) is str:
                return {'http': proxy_for_name, 'https': proxy_for_name, 'ftp': proxy_for_name}
            elif type(proxy_for_name) is dict:
                return proxy_for_name
            else:
                return None

    def _scan_bangumi_in_thread(self):
        logger.debug('start scan bangumi')

        session = SessionManager.Session

        result = session.query(Bangumi).\
            filter(Bangumi.status != Bangumi.STATUS_FINISHED).\
            filter(Bangumi.rss != None)
        try:
            for bangumi in result:
                # update status
                if bangumi.air_date <= datetime.today().date():
                    bangumi.status = Bangumi.STATUS_ON_AIR

                episode_result = session.query(Episode).\
                    filter(Episode.bangumi==bangumi).\
                    filter(Episode.status==Episode.STATUS_NOT_DOWNLOADED)

                http_proxy = self._get_proxy(bangumi.rss)

                task = DMHY(bangumi, episode_result, self.base_path, http_proxy)

                if 'timeout' in self.feedparser:
                    timeout = int(self.feedparser['timeout'])
                else:
                    timeout = None

                task_result = task.parse_feed(timeout)
                if task_result is None:

                    # if bangumi has no not downloaded episode, we consider it's finished.
                    episode_count = session.query(func.count(Episode.id)).\
                        filter(Episode.bangumi==bangumi).\
                        filter(Episode.status==Episode.STATUS_NOT_DOWNLOADED).\
                        scalar()

                    if (bangumi.status == Bangumi.STATUS_ON_AIR) and (episode_count == 0):
                        bangumi.status = Bangumi.STATUS_FINISHED


                    session.commit()
                    logger.debug('scan finished')
                else:
                    logger.warn('scan %s finished with exception', bangumi.id)
                    logger.warn(task_result)


        except OSError as os_error:
            logger.error(os_error)
        except exc.DBAPIError as db_error:
            logger.error(db_error)
            # if connection is invalid rollback the session
            if db_error.connection_invalidated:
                session.rollback()
        except Exception as error:
            logger.error(error)
            traceback.print_exc()

    def scan_bangumi(self):
        threads.deferToThread(self._scan_bangumi_in_thread)


scheduler = Scheduler()

video_manager.set_base_path(scheduler.base_path)

def on_connected(result):
    # logger.info(result)
    scheduler.start()
    info_scanner.start()

def on_connect_fail(result):
    logger.error(result)
    reactor.stop()

d = download_manager.connect()
d.addCallback(on_connected)
d.addErrback(on_connect_fail)

reactor.run()
