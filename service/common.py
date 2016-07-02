import yaml
import json
import os, errno
from urlparse import urlparse

class CommonUtils:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.base_path = config['download']['location']
        self.image_domain = config['domain']['image']
        self.video_domain = config['domain']['video']
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
                print 'create base dir %s successfully' % self.base_path
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                print exception

    def generate_thumbnail_link(self, episode, bangumi):
        thumbnail_url = '/pic/{0}/thumbnails/{1}.png'.format(str(bangumi.id), str(episode.episode_no))
        if self.image_domain is not None:
            thumbnail_url = self.image_domain + thumbnail_url
        return thumbnail_url

    def generate_cover_link(self, bangumi):
        path = urlparse(bangumi.image).path
        extname = os.path.splitext(path)[1]
        cover_url = '/pic/{0}/cover{1}'.format(str(bangumi.id), extname)
        if self.image_domain is not None:
            cover_url = self.image_domain + cover_url
        return cover_url

    def generate_video_link(self, bangumi_id, path):
        video_link = '/video/{0}/{1}'.format(bangumi_id, path.encode('utf-8'))
        if self.video_domain is not None:
            video_link = self.video_domain + video_link
        return video_link


utils = CommonUtils()
