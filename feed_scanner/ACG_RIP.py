import feedparser
from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
import socket
import logging, urllib2

logger = logging.getLogger(__name__)

logger.propagate = True

class ACG_RIP(AbstractScanner):

    def __init__(self, bangumi, episode_list):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.feed_url = 'https://acg.rip/.xml?term=%s'.format((bangumi.acg_rip,))

    def parse_feed(self):
        '''
        parse feed for current bangumi and find not downloaded episode in feed entries.
        this method using an async call to add torrent.
        :param timeout:
        :return: if no error when get feed None is return otherwise return the error object
        '''
        # eps no list
        logger.debug('start scan %s (%s), url is %s', self.bangumi.name, self.bangumi.id, self.bangumi.rss)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        default_timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if self.timeout is not None:
            socket.setdefaulttimeout(self.timeout)

        # use handlers
        if self.proxy is not None:
            proxy_handler = urllib2.ProxyHandler(self.proxy)
            feed_dict = feedparser.parse(self.feed_url, handlers=[proxy_handler])
        else:
            feed_dict = feedparser.parse(self.feed_url)

        # restore the default timeout
        if self.timeout is not None:
            socket.setdefaulttimeout(default_timeout)

        if feed_dict.bozo != 0:
            raise SchedulerError(feed_dict.bozo_exception)

        result_list = []

        for item in feed_dict.entries:
            eps_no = self.parse_episode_number(item['title'])
            if eps_no in eps_no_list:
                result_list.append((item.enclosures[0].href, eps_no))
                # d = self.add_to_download(item, eps_no)
                # d.addCallback(self.download_callback)

        return result_list

    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.acg_rip is not None
