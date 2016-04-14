import feedparser
import re
from utils.DownloadManager import download_manager
from domain.bangumi_model import Episode
from twisted.internet import reactor, threads


class FeedFromDMHY:

    def __init__(self, bangumi, episode_list):
        self.bangumi = bangumi
        self.episode_list = episode_list

    def __parse_episode_number(self, eps_title):
        try:
            search_result = re.search(self.bangumi.eps_regex, eps_title, re.U)
            if search_result and len(search_result.group()):
                return int(search_result.group(1))
            else:
                return -1
        except Exception as exception:
            print(exception)
            return -1

    def parse_feed(self):
        url = self.bangumi.rss
        # eps no list
        eps_no_list = [eps.episode_no for eps in self.episode_list]
        feed_dict = feedparser.parse(url)
        for item in feed_dict.entries:
            eps_no = self.__parse_episode_number(item['title'])
            if eps_no in eps_no_list:
                self.add_to_download(item, eps_no)

    def add_to_download(self, item, eps_no):
        magnet_uri = item.enclosures[0].href
        torrent_file = yield threads.blockingCallFromThread(reactor, download_manager.download, magnet_uri)

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