from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
import logging, urllib, urllib2, json, socket, feedparser

logger = logging.getLogger(__name__)

logger.propagate = True


class LIBYK_SO(AbstractScanner):

    def __init__(self, bangumi, episode_list):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.proxy = self._get_proxy('libyk_so')
        query_dict = json.loads(bangumi.libyk_so, encoding='utf-8')
        t = urllib.quote_plus(query_dict[u't'].replace(u'+', u' ').encode('utf-8'))
        q = urllib.quote_plus(query_dict[u'q'].replace(u'+', u' ').encode('utf-8'))
        self.feed_url = 'https://utils.libyk.com/torrent/rss?m=magnet&t={0}&q={1}'.format(t, q)
        logger.debug(self.feed_url)

    def parse_feed(self):
        '''
        parse feed for current bangumi and find not downloaded episode in feed entries.
        this method using an async call to add torrent.
        :return: if no error when get feed None is return otherwise return the error object
        '''
        logger.debug('start scan %s (%s)', self.bangumi.name, self.bangumi.id)
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
                result_list.append((item.link, eps_no, None, None))

        return result_list

    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.libyk_so is not None
