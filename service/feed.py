# -*- coding: utf-8 -*-

import yaml
import feedparser
import urllib2
import urllib
import socket
import re
import logging

from utils.exceptions import ClientError
from utils.http import json_resp

logger = logging.getLogger(__name__)


class FeedService(object):


    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.feedparser_config = config['feedparser']

        if 'timeout' in self.feedparser_config:
            self.timeout = int(self.feedparser_config['timeout'])
        else:
            self.timeout = None

    def _get_proxy(self, site_name):
        '''
        get the proxy config from config and given url,
        if url specific config is not found using the default config.
        if config is an string, treat it as proxy url, use it for all three schemes
        if config is an dict, make sure it has all scheme set and use it directly
        :param site_name:
        :return: an dict of config
        '''
        if 'proxy' in self.feedparser_config:
            proxy_config = self.feedparser_config['proxy']
            # find config by name, if not found, use default, if default is not set, return None
            if site_name in proxy_config:
                proxy_for_name = proxy_config[site_name]
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

    def parse_episode_number(self, eps_title):
        '''
        parse the episode number from episode title, it use a list of regular expressions. the position in the list
        is the priority of the regular expression.
        :param eps_title: the title of episode.
        :return: episode number if matched, otherwise, -1
        '''
        try:
            regex_tuple = (u'第(\d+)話', u'第(\d+)话', '\[(\d+)(?:v\d)?\]', '\s(\d+)\s', u'【(\d+)(?:v\d)?】')
            for regex in regex_tuple:
                search_result = re.search(regex, eps_title, re.U)
                if search_result is not None:
                    return int(search_result.group(1))

            return -1
        except Exception:
            return -1

    def parse_feed(self, site_name, feed_url):

        proxy = self._get_proxy(site_name)

        default_timeout = socket.getdefaulttimeout()

        # set timeout is provided
        if self.timeout is not None:
            socket.setdefaulttimeout(self.timeout)

        # use handlers
        if proxy is not None:
            proxy_handler = urllib2.ProxyHandler(proxy)
            feed_dict = feedparser.parse(feed_url, handlers=[proxy_handler])
        else:
            feed_dict = feedparser.parse(feed_url)

        # restore the default timeout
        if self.timeout is not None:
            socket.setdefaulttimeout(default_timeout)

        if feed_dict.bozo != 0:
            logger.warn(feed_dict.bozo_exception.getMessage())
            raise ClientError(feed_dict.bozo_exception.getMessage())
        return feed_dict

    def parse_dmhy(self, keywords):
        keywords_encoded = urllib.quote_plus(keywords.replace(u'+', u' ').encode('utf-8'))
        feed_url = 'https://share.dmhy.org/topics/rss/rss.xml?keyword=%s' % (keywords_encoded,)
        feed_dict = self.parse_feed('dmhy', feed_url)
        title_list = []
        for item in feed_dict.entries:
            item_title = item['title']
            eps_no = self.parse_episode_number(item_title)
            title_list.append({'title': item_title, 'eps_no': eps_no})

        return json_resp({'data': title_list, 'status': 0})

    def parse_acg_rip(self, keywords):
        keywords_encoded = urllib.quote_plus(keywords.replace(u'+', u' ').encode('utf-8'))
        feed_url = 'https://acg.rip/.xml?term=%s' % (keywords_encoded,)
        feed_dict = self.parse_feed('acg.rip', feed_url)
        title_list = []
        for item in feed_dict.entries:
            item_title = item['title']
            eps_no = self.parse_episode_number(item_title)
            title_list.append({'title': item_title, 'eps_no': eps_no})

        return json_resp({'data': title_list, 'status': 0})


feed_service = FeedService()
