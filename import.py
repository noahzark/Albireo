# -*- coding: utf-8 -*-

import argparse
import httplib2
import json
from service.admin import admin_service
from utils.SessionManager import SessionManager
from server import app
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.TorrentFile import TorrentFile
import yaml
import os
import re
import uuid
from utils.VideoManager import VideoManager


class ImportTools:
    def __init__(self):
        pass

    # def search_bangumi(self, name=""):
    #     bangumi_tv_url_base = 'http://api.bgm.tv/search/subject/'
    #     bangumi_tv_url_param = '?responseGroup=simple&max_result=10&start=0'
    #     bangumi_tv_url = bangumi_tv_url_base + name + bangumi_tv_url_param
    #     h = httplib2.Http('.cache')
    #     bangumi_tv_url = unicode(bangumi_tv_url, 'utf-8')
    #     (resp, content) = h.request(bangumi_tv_url, 'GET')
    #     if resp.status == 200:
    #         bgm_content = json.loads(content)
    #         list = [bgm for bgm in bgm_content['list'] if bgm['type'] == 2]
    #         if len(list) == 0:
    #             print("No Content Found.")
    #             exit()
    #         bgm_id_list = [bgm['id'] for bgm in list]
    #         bangumi_list = admin_service.get_bangumi_from_bgm_id_list(bgm_id_list)
    #         for bgm in list:
    #             bgm['bgm_id'] = bgm['id']
    #             bgm['id'] = None
    #             # if bgm_id has found in database, give the database id to bgm.id
    #             # that's we know that this bangumi exists in our database
    #             for bangumi in bangumi_list:
    #                 if bgm['bgm_id'] == bangumi.bgm_id:
    #                     bgm['id'] = bangumi.id
    #                     break
    #             bgm['image'] = bgm['images']['large']
    #             # remove useless keys
    #             bgm.pop('images', None)
    #             bgm.pop('collection', None)
    #             bgm.pop('url', None)
    #             bgm.pop('type', None)
    #         for bgm in list:
    #             print(str(bgm['bgm_id']) + '\t' + str(bgm['id']) + '\t' + bgm['name_cn'])
    #     else:
    #         print("Network Error.")
    #         exit()
    #
    # def create_bangumi(self, bgm_id=None):
    #     with app.app_context():
    #         bangumi_list = admin_service.get_bangumi_from_bgm_id_list([bgm_id])
    #         if len(bangumi_list) > 0:
    #             print("Already Created Bangumi. Exit.")
    #             print("Dir is at :")
    #             fr = open('./config/config.yml', 'r')
    #             config = yaml.load(fr)
    #             print(config['download']['location'] + '/' + str(bangumi_list[0][0]))
    #             exit()
    #         bangumi_tv_url_base = 'http://api.bgm.tv/subject/'
    #         bangumi_tv_url_param = '?responseGroup=large'
    #         if bgm_id is not None:
    #             bgm_id = str(bgm_id)
    #             bangumi_tv_url = bangumi_tv_url_base + bgm_id + bangumi_tv_url_param
    #             h = httplib2.Http('.cache')
    #             (resp, content) = h.request(bangumi_tv_url, 'GET')
    #             content = json.loads(content)
    #             bangumi = Bangumi(bgm_id=content['id'],
    #                               name=content['name'],
    #                               name_cn=content['name_cn'],
    #                               summary=content['summary'],
    #                               eps=len(content['eps']),
    #                               image=content['images']['large'],
    #                               air_date=content['air_date'],
    #                               air_weekday=content['air_weekday'],
    #                               status=Bangumi.STATUS_FINISHED)
    #             session = SessionManager.Session()
    #             session.add(bangumi)
    #             for eps_item in content['eps']:
    #                 eps = Episode(bgm_eps_id=eps_item['id'],
    #                               episode_no=eps_item['sort'],
    #                               name=eps_item['name'],
    #                               name_cn=eps_item['name_cn'],
    #                               duration=eps_item['duration'],
    #                               airdate=eps_item['airdate'],
    #                               status=Episode.STATUS_NOT_DOWNLOADED)
    #                 bangumi.episodes.append(eps)
    #             # session = SessionManager.Session()
    #             session.commit()
    #             bangumi_id = str(bangumi.id)
    #             print("Dir is at :")
    #             fr = open('./config/config.yml', 'r')
    #             config = yaml.load(fr)
    #             print(config['download']['location'] + '/' + str(bangumi_id))
    #         else:
    #             print("Network Error.")
    #             exit()

    def __add_to_torrent_file(self, session, torrent_files, eps_id, path):
        try:
            torrent_files_of_eps = session.query(TorrentFile).filter(TorrentFile.episode_id == eps_id).all()
            torrent_files_of_eps[0].file_path = path
        except Exception:
            torrent_files.append(TorrentFile(episode_id=eps_id, file_path=path, torrent_id=uuid.uuid4()))

    def update_bangumi(self, bangumi_id=None):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        download_dir = config['download']['location'] + '/' + str(bangumi_id)
        files = os.listdir(download_dir)

        session = SessionManager.Session()
        eps_list = session.query(Episode).filter(Episode.bangumi_id == bangumi_id).all()

        episodes = {}
        torrent_files = []
        for eps in eps_list:
            episodes[eps.episode_no] = eps
            episode_num = str(eps.episode_no)
            if len(episode_num) == 1:
                episode_num = '0' + episode_num
            for f in files:
                if re.search('\[' + episode_num + '\]', f):
                    eps.status = Episode.STATUS_DOWNLOADED
                    self.__add_to_torrent_file(session, torrent_files, eps.id, f)
                    break
        while True:
            for eps in episodes.values():
                if not eps:
                    continue
                episode_num = str(eps.episode_no)
                file_name = "None"
                for torrent_file in torrent_files:
                    if torrent_file.episode_id == eps.id:
                        file_name = torrent_file.file_path
                        break
                print (episode_num + ": \t" + file_name)

            print("Right? Y/N")
            x = raw_input(">>> Input: ")
            if x == "Y":
                video_manager = VideoManager()
                video_manager.set_base_path(config['download']['location'])
                for f in torrent_files:
                    for eps in episodes.values():
                        if eps.id == f.episode_id:
                            video_manager.create_episode_thumbnail(eps, f.file_path, '00:00:01.000')
                            break
                    session.add(f)
                session.commit()
                return
            else:
                torrent_files = []
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
                    self.__add_to_torrent_file(session, torrent_files, eps.id, f)


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
