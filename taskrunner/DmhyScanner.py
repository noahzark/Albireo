from taskrunner.BangumiScanner import BangumiScanner
from feed_scanner.DMHY import DMHY
from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi

import traceback
import logging

logger = logging.getLogger(__name__)

class DmhyScanner(BangumiScanner):

    def __init__(self, base_path, interval):
        super(self.__class__, self).__init__(base_path, interval)

    def query_bangumi_list(self):
        session = SessionManager.Session()
        try:
            bangumi_list = session.query(Bangumi).\
                filter(Bangumi.status != Bangumi.STATUS_FINISHED).\
                filter(Bangumi.dmhy != None).all()
            return [bangumi for bangumi in bangumi_list if bangumi.dmhy]
        except Exception as error:
            logger.error(error, exc_info=True)
            return []
        finally:
            SessionManager.Session.remove()

    def scan_feed(self, bangumi, episode_list):
        try:
            dmhy = DMHY(bangumi, episode_list)
            return dmhy.parse_feed()
        except Exception as error:
            logger.error(error, exc_info=True)
            return None
