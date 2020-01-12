from taskrunner.BangumiScanner import BangumiScanner
from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi
from feed_scanner.UNIVERSAL import UNIVERSAL
import json
import traceback
import logging

logger = logging.getLogger(__name__)


class UniversalScanner(BangumiScanner):

    def __init__(self, base_path, interval, mode):
        super(self.__class__, self).__init__(base_path, interval)
        self.mode = mode

    def query_bangumi_list(self):
        session = SessionManager.Session()
        try:
            bangumi_list = session.query(Bangumi).\
                filter(Bangumi.status != Bangumi.STATUS_FINISHED).\
                filter(Bangumi.universal != None).all()
            result_list = []
            for bangumi in bangumi_list:
                if bangumi.universal:
                    res_list = json.loads(bangumi.universal)
                    for res in res_list:
                        if res['mode'] == self.mode:
                            result_list.append(bangumi)
                            break
            return result_list
        except Exception as error:
            logger.error(error, exc_info=True)
            return []
        finally:
            SessionManager.Session.remove()

    def scan_feed(self, bangumi, episode_list):
        try:
            universal = UNIVERSAL(bangumi, episode_list, self.mode)
            return universal.parse_feed()
        except Exception as error:
            logger.error(error, exc_info=True)
            return None
