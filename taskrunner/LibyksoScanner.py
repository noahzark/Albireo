from domain.Bangumi import Bangumi
from taskrunner.BangumiScanner import BangumiScanner
from utils.SessionManager import SessionManager
from feed_scanner.LIBYK_SO import LIBYK_SO

import traceback
import logging

logger = logging.getLogger(__name__)

class LibyksoScanner(BangumiScanner):

    def __init__(self, base_path, interval):
        super(self.__class__, self).__init__(base_path, interval)

    def query_bangumi_list(self):
        session = SessionManager.Session()
        try:
            bangumi_list = session.query(Bangumi).\
                filter(Bangumi.status != Bangumi.STATUS_FINISHED).\
                filter(Bangumi.libyk_so != None).\
                all()
            return [bangumi for bangumi in bangumi_list if bangumi.libyk_so]
        except Exception as error:
            logger.error(error, exc_info=True)
            return []
        finally:
            SessionManager.Session.remove()

    def scan_feed(self, bangumi, episode_list):
        try:
            libyk_so = LIBYK_SO(bangumi, episode_list)
            return libyk_so.parse_feed()
        except Exception as error:
            logger.error(error, exc_info=True)
            return None
