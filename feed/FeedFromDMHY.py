import feedparser
import re
from utils.DownloadManager import download_manager
from utils.exceptions import SchedulerError
from domain.Episode import Episode
from twisted.internet import reactor, threads
from twisted.internet.defer import inlineCallbacks, returnValue
import os, errno, socket
import logging, urllib2
from urlparse import urlparse

logger = logging.getLogger(__name__)

logger.propagate = True

class FeedFromDMHY:

    def __init__(self, bangumi, episode_list, base_path, proxy=None):
        self.bangumi = bangumi
        self.episode_list = episode_list
        self.bangumi_path = base_path + '/' + str(self.bangumi.id)
        self.proxy = proxy
        try:
            # create an path for bangumi using bangumi.id
            if not os.path.exists(self.bangumi_path):
                os.makedirs(self.bangumi_path)
                info_file = open(self.bangumi_path + '/info.txt', 'w')
                info_file.write(self.bangumi.name.encode('utf-8'))
                info_file.close()
                logger.info('create dir for %s', self.bangumi.name)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise exception

    def __parse_episode_number(self, eps_title):
        '''
        parse the episode number from episode title using bangumi.regex regular expression
        :param eps_title:
        :return: the episode number if no episode number is found or any exception occurred -1 is returned
        '''
        try:
            search_result = re.search(self.bangumi.eps_regex, eps_title, re.U)
            if search_result and len(search_result.group()):
                return int(search_result.group(1))
            else:
                return -1
        except Exception as exception:
            logger.warn(exception)
            return -1

    def parse_feed(self, timeout=None):
        '''
        parse feed for current bangumi and find not downloaded episode in feed entries.
        this method using an async call to add torrent.
        :param timeout:
        :return: if no error when get feed None is return otherwise return the error object
        '''
        url = self.bangumi.rss
        # eps no list
        logger.debug('start scan %s (%s), url is %s', self.bangumi.name, self.bangumi.id, self.bangumi.rss)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        default_timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if timeout is not None:
            socket.setdefaulttimeout(timeout)

        # use handlers
        if self.proxy is not None:
            print self.proxy
            proxy_handler = urllib2.ProxyHandler(self.proxy)
            feed_dict = feedparser.parse(url, handlers=[proxy_handler])
        else:
            feed_dict = feedparser.parse(url)

        # restore the default timeout
        if timeout is not None:
            socket.setdefaulttimeout(default_timeout)

        if feed_dict.bozo != 0:
            print feed_dict
            return feed_dict.bozo_exception

        for item in feed_dict.entries:
            eps_no = self.__parse_episode_number(item['title'])
            if eps_no in eps_no_list:
                d = self.add_to_download(item, eps_no)
                d.addCallback(self.download_callback)

    @inlineCallbacks
    def add_to_download(self, item, eps_no):
        '''
        add current episode to download, when download is added, update episode status and add torrent_file record
        :param item: the item of corresponding episode, it contains an enclosure list which has magnet uri
        :param eps_no: the episode number
        :return: the episode number, the return value is useless
        '''
        magnet_uri = item.enclosures[0].href
        torrent_file = yield threads.blockingCallFromThread(reactor, download_manager.download, magnet_uri, self.bangumi_path)

        if torrent_file is None:
            logger.warn('episode %s of %s added failed', eps_no, self.bangumi.name)
            returnValue(eps_no)
        else:
            print torrent_file.torrent_id

            episode = None
            for eps in self.episode_list:
                if eps_no == eps.episode_no:
                    episode = eps
                    break

            if episode.torrent_files is not list:
                episode.torrent_files = []

            episode.torrent_files.append(torrent_file)

            episode.status = Episode.STATUS_DOWNLOADING

            logger.info('episode %s of %s added', eps_no, self.bangumi.name)

            returnValue(eps_no)

    def download_callback(self, eps_no):
        pass