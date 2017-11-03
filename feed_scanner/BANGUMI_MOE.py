from feed_scanner.AbstractScanner import AbstractScanner
from utils.exceptions import SchedulerError
import json, socket, requests, os

import logging

logger = logging.getLogger(__name__)

class BANGUMI_MOE(AbstractScanner):

    def __init__(self, bangumi, episode_list):
        super(self.__class__, self).__init__(bangumi, episode_list)
        self.proxy = self._get_proxy('bangumi_moe')
        self.feed_url = 'https://bangumi.moe/api/torrent/search'
        tag_list = json.loads(bangumi.bangumi_moe)
        self.tag_list = [tag['_id'] for tag in tag_list]

    def parse_feed(self):
        logger.debug('start scan %s (%s)', self.bangumi.name, self.bangumi.id)
        eps_no_list = [eps.episode_no for eps in self.episode_list]

        timeout = socket.getdefaulttimeout()
        # set timeout is provided
        if self.timeout is not None:
            timeout = self.timeout

        r = requests.post(self.feed_url, json={'tag_id': self.tag_list}, timeout=timeout)

        if r.status_code > 399:
            raise SchedulerError('Network Error %d'.format(r.status_code))

        resp_body = r.json()

        result_list = []

        for torrent in resp_body['torrents']:
            eps_list = []
            for content_file in torrent['content']:
                file_path = content_file[0]
                file_name = os.path.basename(file_path)
                if not file_name.endswith('.mp4'):
                    continue
                eps_no = self.parse_episode_number(file_name)
                if eps_no in eps_no_list:
                    eps_list.append({
                        'eps_no': eps_no,
                        'file_path': file_path,
                        'file_name': file_name
                    })
            if len(eps_list) == 0:
                continue
            torrent_url = self.generate_torrent_url(torrent['_id'], eps_list)
            for eps in eps_list:
                result_list.append((torrent_url, eps['eps_no'], eps['file_path'], eps['file_name']))

        logger.debug(result_list)

        return result_list

    def generate_torrent_url(self, torrent_id, eps_list):
        if len(eps_list) > 1:
            eps_no_format = '{0}-{1}'.format(str(eps_list[0]['eps_no']), str(eps_list[-1]['eps_no']))
        else:
            eps_no_format = str(eps_list[0]['eps_no'])
        return 'https://bangumi.moe/download/torrent/{0}/{1}-{2}.torrent'.format(
            torrent_id, str(self.bangumi.id), eps_no_format)


    @classmethod
    def has_keyword(cls, bangumi):
        return bangumi.bangumi_moe is not None
