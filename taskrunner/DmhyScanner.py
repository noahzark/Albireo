from taskrunner.BangumiScanner import BangumiScanner
from feed_scanner.DMHY import DMHY

import logging

logger = logging.getLogger(__name__)
logger.propagate = True

class DmhyScanner(BangumiScanner):

    def __init__(self, base_path, interval):
        super(self.__class__, self).__init__(base_path, interval)

    def has_keyword(self, bangumi):
        return bangumi.dmhy is not None

    def scan_feed(self, bangumi, episode_list):
        try:
            dmhy = DMHY(bangumi, episode_list)
            return dmhy.parse_feed()
        except Exception as error:
            logger.warn(error)
