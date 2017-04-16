# -*- coding: utf-8 -*-
import logging, urllib, socket, feedparser, cfscrape, os
from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
from utils.scraper import DMHYFileListScraper
from urlparse import urlparse, urlunparse
logger = logging.getLogger(__name__)

logger.propagate = True

class DMHY(AbstractScanner):

    def __init__(self, bangumi, episode_list):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.proxy = self._get_proxy('dmhy')
        keywords = urllib.quote_plus(bangumi.dmhy.replace(u'+', u' ').encode('utf-8'))
        self.feed_url = 'https://share.dmhy.org/topics/rss/rss.xml?keyword=%s' % (keywords,)
        logger.debug(self.feed_url)
        logger.debug(self.proxy)

    def _ensure_https(self, url):
        o = urlparse(url)
        if o.scheme == 'http':
            l = list(o)
            l[0] = 'https'
            return urlunparse(tuple(l))
        else:
            return url

    def parse_feed(self):
        '''
        parse feed for current bangumi and find not downloaded episode in feed entries.
        this method using an async call to add torrent.
        :return: if no error when get feed None is return otherwise return the error object
        '''
        # eps no list
        logger.debug('start scan %s (%s)', self.bangumi.name, self.bangumi.id)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if self.timeout is not None:
            timeout = self.timeout

        scraper = cfscrape.create_scraper()

        r = scraper.get(self.feed_url, proxies=self.proxy, timeout=timeout)

        if r.status_code > 399:
            raise SchedulerError('Network Error %d'.format(r.status_code))

        feed_dict = feedparser.parse(r.text)

        if feed_dict.bozo != 0:
            raise SchedulerError(feed_dict.bozo_exception)

        result_list = []

        for item in feed_dict.entries:
            item_link = self._ensure_https(item['link'])
            logger.debug('link %s', item_link)
            link_r = scraper.get(item_link, proxies=self.proxy)
            if link_r.status_code > 399:
                logger.warn('Network Error %d'.format(link_r.status_code))

            dmhy_scraper = DMHYFileListScraper()
            dmhy_scraper.feed(r.text)
            file_path_list = dmhy_scraper.file_path_list
            for file_path in file_path_list:
                file_name = os.path.basename(file_path)
                eps_no = self.parse_episode_number(file_name)
                if eps_no in eps_no_list:
                    result_list.append((item.enclosures[0].href, eps_no, file_path, file_name))

        return result_list

    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.dmhy is not None
