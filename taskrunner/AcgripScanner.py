from taskrunner.BangumiScanner import BangumiScanner
from feed_scanner.ACG_RIP import ACG_RIP
from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi

import traceback
import logging

logger = logging.getLogger(__name__)
logger.propagate = True

class AcgripScanner(BangumiScanner):

    def __init__(self, base_path, interval):
        super(self.__class__, self).__init__(base_path, interval)

    def query_bangumi_list(self):
        session = SessionManager.Session()
        try:
            bangumi_list = session.query(Bangumi).\
                filter(Bangumi.status != Bangumi.STATUS_FINISHED).\
                filter(Bangumi.acg_rip != None).all()
            return [bangumi for bangumi in bangumi_list if bangumi.acg_rip]
        except Exception as error:
            logger.error(error, exc_info=True)
            return []
        finally:
            SessionManager.Session.remove()

    def scan_feed(self, bangumi, episode_list):
        try:
            acg_rip = ACG_RIP(bangumi, episode_list)
            return acg_rip.parse_feed()
        except Exception as error:
            logger.error(error, exc_info=True)
            return None
