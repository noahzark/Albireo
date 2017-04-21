# -*- coding: utf-8 -*-

import argparse
from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi
from domain.Favorites import Favorites
from domain.WatchProgress import WatchProgress
from domain.Episode import Episode
from domain.VideoFile import VideoFile
import yaml
import os
import re
from utils.VideoManager import VideoManager
from utils.constants import episode_regex_tuple


class ImportTools:
    def __init__(self):
        pass

    def __parse_episode_number(self, eps_title):
        '''
        parse the episode number from episode title, it use a list of regular expressions. the position in the list
        is the priority of the regular expression.
        :param eps_title: the title of episode.
        :return: episode number if matched, otherwise, -1
        '''
        try:
            for regex in episode_regex_tuple:
                search_result = re.search(regex, eps_title, re.U | re.I)
                if search_result is not None:
                    return int(search_result.group(1))

            return -1
        except Exception:
            return -1

    def __episode_has_video_file(self, existed_video_files, eps):
        for video_file in existed_video_files:
            if video_file.episode_id == eps.id:
                return True

        return False

    def update_bangumi(self, bangumi_id=None):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        download_dir = config['download']['location'] + '/' + str(bangumi_id)
        files = os.listdir(download_dir)

        session = SessionManager.Session()
        eps_list = session.query(Episode).\
            filter(Episode.bangumi_id == bangumi_id).all()

        existed_video_files = session.query(VideoFile).filter(VideoFile.bangumi_id == bangumi_id).all()

        episodes = {}
        video_files = []
        for eps in eps_list:
            if self.__episode_has_video_file(existed_video_files, eps):
                continue
            episodes[eps.episode_no] = eps
            for f in files:
                if self.__parse_episode_number(f) == eps.episode_no:
                    eps.status = Episode.STATUS_DOWNLOADED
                    video_files.append(VideoFile(bangumi_id=bangumi_id,
                                                 episode_id=eps.id,
                                                 file_path=f.decode('utf-8'),
                                                 status=VideoFile.STATUS_DOWNLOADED))
                    break
        while True:
            for eps in episodes.values():
                if not eps:
                    continue
                episode_num = str(eps.episode_no)
                file_name = "None"
                for video_file in video_files:
                    if video_file.episode_id == eps.id:
                        file_name = video_file.file_path
                        break
                print (episode_num + ": \t" + file_name)

            print("Right? Y/N")
            x = raw_input(">>> Input: ")
            if x == "Y":
                video_manager = VideoManager()
                video_manager.set_base_path(config['download']['location'])
                for video_file in video_files:
                    for eps in episodes.values():
                        if eps.id == video_file.episode_id:
                            video_manager.create_episode_thumbnail(eps, video_file.file_path, '00:00:01.000')
                            meta_dict = video_manager.get_video_meta(u'{0}/{1}/{2}'.format(video_manager.base_path, bangumi_id.encode('utf-8'), video_file.file_path))
                            if meta_dict is not None:
                                video_file.resolution_w = meta_dict['width']
                                video_file.resolution_h = meta_dict['height']
                                video_file.duration = meta_dict['duration']
                                session.add(video_file)
                            break
                session.commit()
                return
            else:
                video_files = []
                for f in files:
                    print f
                    x = raw_input(">>> Episode Num")
                    if not x:
                        continue
                    x = int(x)
                    eps = episodes[x]
                    if not eps:
                        continue
                    eps.status = Episode.STATUS_DOWNLOADED
                    video_files.append(VideoFile(bangumi_id=bangumi_id,
                                                 episode_id=eps.id,
                                                 file_path=f.decode('utf-8'),
                                                 status=VideoFile.STATUS_DOWNLOADED))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import Bangumi Tools.')
    sub_parsers = parser.add_subparsers(dest='operate')
    search_parser = sub_parsers.add_parser("search", help="Search Bangumi")
    search_parser.add_argument('name', type=str, help='Name of Bangumi')
    create_parser = sub_parsers.add_parser("create", help="Create Bangumi")
    create_parser.add_argument('id', type=int, help='Bangumi Id')
    update_parser = sub_parsers.add_parser("update", help="Update Bangumi")
    update_parser.add_argument('uuid', type=str, help='Bangumi UUID')
    args = parser.parse_args()

    import_tools = ImportTools()
    if args.operate == 'search':
        # import_tools.search_bangumi(args.name)
        print 'search bangumi not supported, please use web admin'
    elif args.operate == 'create':
        # import_tools.create_bangumi(args.id)
        print 'create bangumi not supported, please use web admin'
    elif args.operate == 'update':
        import_tools.update_bangumi(args.uuid)
