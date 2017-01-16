# for video related operations
import subprocess32 as subprocess
import logging
import os, errno

logger = logging.getLogger(__name__)


class VideoManager:

    def __init__(self):
        self.base_path = None

    def set_base_path(self, path):
        self.base_path = path

    def create_thumbnail(self, video_path, time, output_path):
        try:
            subprocess.check_call(['ffmpeg',
                                   '-y',
                                   '-ss',
                                   time,
                                   '-i',
                                   b'{0}'.format(video_path.encode('utf-8')),
                                   '-vframes',
                                   '1',
                                   output_path])
            return True
        except subprocess.CalledProcessError as error:
            logger.warn(error)
            return False


    def create_episode_thumbnail(self, episode, relative_path, time):
        bangumi_id = str(episode.bangumi_id)
        video_path = u'{0}/{1}/{2}'.format(self.base_path, bangumi_id, relative_path)
        thumbnail_folder = u'{0}/{1}/thumbnails'.format(self.base_path, bangumi_id)
        output_path = u'{0}/{1}.png'.format(thumbnail_folder, str(episode.episode_no))
        try:
            if not os.path.exists(thumbnail_folder):
                os.makedirs(thumbnail_folder)
                logger.info('create base dir %s successfully', thumbnail_folder)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                logger.error(exception)

        return self.create_thumbnail(video_path, time, output_path)


video_manager = VideoManager()
