# for video related operations
import subprocess32 as subprocess
import logging
import os, errno
import json

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
            return output_path
        except subprocess.CalledProcessError as error:
            logger.error(error, exc_info=True)
            return output_path

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

    def get_video_meta(self, video_path):
        """
        get video meta information
        :param video_path: the absolute path of video file
        :return: a dictionary
            {
                'width': integer,
                'height':  integer,
                'duration': integer (millisecond)
            }

        if an error occurred, this method will return None
        """
        try:
            output = subprocess.check_output([
                'ffprobe',
                '-v',
                'error',
                '-show_entries',
                'format=duration:stream=width:stream=height',
                '-select_streams',
                'v:0',
                '-of',
                'json',
                b'{0}'.format(video_path.encode('utf-8'))
            ])
            meta = json.loads(output)
            result = {}
            if 'format' in meta and 'duration' in meta['format']:
                result['duration'] = int(float(meta['format']['duration']) * 1000)
            if 'streams' in meta and len(meta['streams']) and 'width' in meta['streams'][0] and 'height' in meta['streams'][0]:
                result['width'] = meta['streams'][0]['width']
                result['height'] = meta['streams'][0]['height']
            return result
        except subprocess.CalledProcessError as error:
            logger.error(error)
            return None


video_manager = VideoManager()
