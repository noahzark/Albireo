# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound

from domain.Episode import Episode
from domain.Bangumi import Bangumi
from domain.Image import Image
from domain.TorrentFile import TorrentFile
from domain.VideoFile import VideoFile
from datetime import datetime
from utils.SessionManager import SessionManager
from utils.exceptions import ClientError
from utils.http import json_resp, FileDownloader, bangumi_request
from utils.db import row2dict
from sqlalchemy.sql.expression import or_, desc, asc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import joinedload
import yaml
import json
import os, errno
from urlparse import urlparse
from utils.VideoManager import video_manager
from service.common import utils
from utils.image import get_dominant_color, get_dimension
# from werkzeug.utils import secure_filename

import logging

logger = logging.getLogger(__name__)


class AdminService:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.base_path = config['download']['location']
        self.image_domain = config['domain']['image']
        self.file_downloader = FileDownloader()

        self.delete_delay = {'bangumi': 10, 'episode': 1}

        if config['task'].get('delete_delay') is None:
            logger.warn('delete_delay section is not set, please update your config file')
        else:
            self.delete_delay = config['task'].get('delete_delay')

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

    def __get_eps_len(self, eps):
        EPISODE_TYPE = 0 # episode type = 0 is the normal episode type, even the episode is not a 24min length
        eps_length = 0
        for eps_item in eps:
            if eps_item['type'] == EPISODE_TYPE:
                eps_length = eps_length + 1

        return eps_length

    def __get_bangumi_status(sefl, air_date):
        _air_date = datetime.strptime(air_date, '%Y-%m-%d')
        _today = datetime.today()
        if _today >= _air_date:
            return Bangumi.STATUS_ON_AIR
        else:
            return Bangumi.STATUS_PENDING

    def __save_bangumi_cover(self, bangumi):
        if not bangumi.image:
            return
        bangumi_path = self.base_path + '/' + str(bangumi.id)
        try:
            if not os.path.exists(bangumi_path):
                os.makedirs(bangumi_path)
                print 'create base dir %s successfully' % self.base_path
        except OSError as exception:
            if exception.errno == errno.EACCES:
                # permission denied
                raise exception
            else:
                print exception

        path = urlparse(bangumi.image).path
        extname = os.path.splitext(path)[1]
        cover_path = '{0}/cover{1}'.format(str(bangumi.id), extname)
        file_path = '{0}/{1}'.format(self.base_path, cover_path)
        self.file_downloader.download_file(bangumi.image, file_path)
        return file_path, cover_path

    def search_bangumi(self, type, term, offset, count):
        """
        search bangumi from bangumi.tv, properly handling cookies is required for the bypass anti-bot mechanism
        :param term: a urlencoded word of the search term.
        :return: a json object
        """

        result = {"data": [], "total": 0}
        api_url = 'http://api.bgm.tv/search/subject/{0}?responseGroup=large&max_result={1}&start={2}&type={3}'.format(term.encode('utf-8'), count, offset, type)
        r = bangumi_request.get(api_url)

        if r.status_code > 399:
            r.raise_for_status()

        try:
            bgm_content = r.json()
        except Exception as error:
            logger.warn(error)
            result['message'] = 'fail to query bangumi'
            return json_resp(result, 500)

        if 'code' in bgm_content and bgm_content['code'] == 404:
            return json_resp(result, 200)

        bgm_list = bgm_content['list']
        total_count = bgm_content['results']
        if len(bgm_list) == 0:
            return json_resp(result)

        bgm_id_list = [bgm['id'] for bgm in bgm_list]
        bangumi_list = self.get_bangumi_from_bgm_id_list(bgm_id_list)

        for bgm in bgm_list:
            bgm['bgm_id'] = bgm.get('id')
            bgm['id'] = None
            # if bgm_id has found in database, give the database id to bgm.id
            # that's we know that this bangumi exists in our database
            for bangumi in bangumi_list:
                if bgm['bgm_id'] == bangumi.bgm_id:
                    bgm['id'] = bangumi.id
                    break
            bgm_images = bgm.get('images')
            if bgm_images:
                bgm['image'] = bgm_images.get('large')
            # remove useless keys
            bgm.pop('images', None)
            bgm.pop('collection', None)
            bgm.pop('url', None)
            bgm.pop('type', None)

        result['data'] = bgm_list
        result['total'] = total_count
        return json_resp(result)

    def query_bangumi_detail(self, bgm_id):

        api_url = 'http://api.bgm.tv/subject/' + bgm_id + '?responseGroup=large'
        r = bangumi_request.get(api_url)

        if r.status_code > 399:
            r.raise_for_status()

        return r.text

    def list_bangumi(self, page, count, sort_field, sort_order, name):
        try:
            session = SessionManager.Session()
            query_object = session.query(Bangumi).\
                options(joinedload(Bangumi.cover_image)).\
                filter(Bangumi.delete_mark == None)

            if name is not None:
                name_pattern = '%{0}%'.format(name.encode('utf-8'),)
                logger.debug(name_pattern)
                query_object = query_object.\
                    filter(or_(Bangumi.name.ilike(name_pattern), Bangumi.name_cn.ilike(name_pattern)))
                # count total rows
                total = session.query(func.count(Bangumi.id)).\
                    filter(or_(Bangumi.name.ilike(name_pattern), Bangumi.name_cn.ilike(name_pattern))).\
                    scalar()
            else:
                total = session.query(func.count(Bangumi.id)).scalar()

            if sort_order == 'desc':
                query_object = query_object.\
                    order_by(desc(getattr(Bangumi, sort_field)))
            else:
                query_object = query_object.\
                    order_by(asc(getattr(Bangumi, sort_field)))

            # we now support query all method by passing count = -1
            if count == -1:
                bangumi_list = query_object.all()
            else:
                offset = (page - 1) * count
                bangumi_list = query_object.offset(offset).limit(count).all()

            bangumi_dict_list = []
            for bgm in bangumi_list:
                bangumi = row2dict(bgm)
                bangumi['cover'] = utils.generate_cover_link(bgm)
                utils.process_bangumi_dict(bgm, bangumi)
                bangumi_dict_list.append(bangumi)

            return json_resp({'data': bangumi_dict_list, 'total': total})
            # raise ClientError('something happened')
        finally:
            SessionManager.Session.remove()

    def add_bangumi(self, content):
        try:
            bangumi_data = json.loads(content)

            bangumi = Bangumi(bgm_id=bangumi_data.get('bgm_id'),
                              name=bangumi_data.get('name'),
                              name_cn=bangumi_data.get('name_cn'),
                              type=bangumi_data.get('type'),
                              summary=bangumi_data.get('summary'),
                              eps=bangumi_data.get('eps'),
                              image=bangumi_data.get('image'),
                              air_date=bangumi_data.get('air_date'),
                              air_weekday=bangumi_data.get('air_weekday'),
                              status=self.__get_bangumi_status(bangumi_data.get('air_date')))


            # bangumi.dmhy = bangumi_data.get('dmhy')
            # bangumi.acg_rip = bangumi_data.get('acg_rip')
            # bangumi.libyk_so = bangumi_data.get('libyk_so')

            bangumi.eps_no_offset = bangumi_data.get('eps_no_offset')

            session = SessionManager.Session()

            session.add(bangumi)

            bangumi.episodes = []

            for eps_item in bangumi_data['episodes']:
                eps = Episode(bgm_eps_id=eps_item.get('bgm_eps_id'),
                              episode_no=eps_item.get('episode_no'),
                              name=eps_item.get('name'),
                              name_cn=eps_item.get('name_cn'),
                              duration=eps_item.get('duration'),
                              status=Episode.STATUS_NOT_DOWNLOADED)
                if eps_item.get('airdate') != '':
                    eps.airdate=eps_item.get('airdate')

                eps.bangumi = bangumi
                bangumi.episodes.append(eps)

            session.commit()

            bangumi_id = str(bangumi.id)
            try:
                (cover_file_path, cover_path) = self.__save_bangumi_cover(bangumi)
                # get dominant color
                bangumi.cover_color = get_dominant_color(cover_file_path)
                (width, height) = get_dimension(cover_file_path)
                bangumi.cover_image = Image(file_path=cover_path,
                                            dominant_color=bangumi.cover_color,
                                            width=width,
                                            height=height)
                session.commit()
            except Exception as error:
                logger.warn(error)

            return json_resp({'data': {'id': bangumi_id}})
        finally:
            SessionManager.Session.remove()

    def update_bangumi(self, bangumi_id, bangumi_dict):
        try:
            session = SessionManager.Session()
            bangumi = session.query(Bangumi).\
                filter(Bangumi.id == bangumi_id).\
                filter(Bangumi.delete_mark == None).\
                one()

            bangumi.name = bangumi_dict['name']
            bangumi.name_cn = bangumi_dict['name_cn']
            bangumi.summary = bangumi_dict['summary']
            bangumi.eps = bangumi_dict['eps']
            # bangumi.eps_regex = bangumi_dict['eps_regex']
            bangumi.image = bangumi_dict['image']
            bangumi.air_date = datetime.strptime(bangumi_dict['air_date'], '%Y-%m-%d')
            bangumi.air_weekday = bangumi_dict['air_weekday']
            # bangumi.rss = bangumi_dict['rss']
            bangumi.status = bangumi_dict['status']

            bangumi.dmhy = bangumi_dict.get('dmhy')
            bangumi.acg_rip = bangumi_dict.get('acg_rip')
            bangumi.libyk_so = bangumi_dict.get('libyk_so')
            bangumi.bangumi_moe = bangumi_dict.get('bangumi_moe')

            bangumi.eps_no_offset = bangumi_dict.get('eps_no_offset')
            if not bangumi.eps_no_offset:
                # in case the eps_no_offset is empty string
                bangumi.eps_no_offset = None


            bangumi.update_time = datetime.now()

            session.commit()

            return json_resp({'msg': 'ok'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND)
        finally:
            SessionManager.Session.remove()

    def get_bangumi(self, id):
        try:
            session = SessionManager.Session()

            bangumi = session.query(Bangumi).\
                options(joinedload(Bangumi.episodes).joinedload(Episode.thumbnail_image)).\
                options(joinedload(Bangumi.cover_image)).\
                filter(Bangumi.id == id).\
                filter(Bangumi.delete_mark == None).\
                one()

            episodes = []

            for episode in bangumi.episodes:
                if episode.delete_mark is not None:
                    continue
                eps = row2dict(episode)
                eps['thumbnail'] = utils.generate_thumbnail_link(episode, bangumi)
                utils.process_episode_dict(episode, eps)
                episodes.append(eps)

            bangumi_dict = row2dict(bangumi)

            bangumi_dict['episodes'] = episodes
            utils.process_bangumi_dict(bangumi, bangumi_dict)

            bangumi_dict['cover'] = utils.generate_cover_link(bangumi)

            return json_resp({'data': bangumi_dict})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        except Exception as exception:
            raise exception
        finally:
            SessionManager.Session.remove()

    def delete_bangumi(self, bangumi_id):
        try:
            session = SessionManager.Session()

            bangumi = session.query(Bangumi).filter(Bangumi.id == bangumi_id).one()

            bangumi.delete_mark = datetime.now()

            session.commit()

            return json_resp({'data': {'delete_delay': self.delete_delay['bangumi']}})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def get_bangumi_from_bgm_id_list(self, bgm_id_list):
        s = select([Bangumi.id, Bangumi.bgm_id]).where(Bangumi.bgm_id.in_(bgm_id_list) & (Bangumi.delete_mark == None)).select_from(Bangumi)
        return SessionManager.engine.execute(s).fetchall()

    def add_episode(self, episode_dict):
        try:
            session = SessionManager.Session()
            episode = Episode(bangumi_id=episode_dict['bangumi_id'],
                              bgm_eps_id=episode_dict.get('bgm_eps_id', -1),
                              episode_no=episode_dict['episode_no'],
                              name=episode_dict.get('name'),
                              name_cn=episode_dict.get('name_cn'),
                              duration=episode_dict.get('duration'),
                              airdate=episode_dict.get('airdate'),
                              status=Episode.STATUS_NOT_DOWNLOADED)
            session.add(episode)
            session.commit()
            episode_id = str(episode.id)
            return json_resp({'data': {'id': episode_id}})
        finally:
            SessionManager.Session.remove()

    def update_episode(self, episode_id, episode_dict):
        try:
            session = SessionManager.Session()
            episode = session.query(Episode).filter(Episode.id == episode_id).one()
            episode.name = episode_dict['name']
            episode.name_cn = episode_dict['name_cn']
            episode.airdate = datetime.strptime(episode_dict['airdate'], '%Y-%m-%d')
            episode.duration = episode_dict['duration']
            episode.update_time = datetime.now()

            if 'status' in episode_dict:
                episode.status = episode_dict['status']

            session.commit()

            return json_resp({'msg': 'ok'})

        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def get_episode(self, episode_id):
        try:
            session = SessionManager.Session()
            episode = session.query(Episode).\
                options(joinedload(Episode.thumbnail_image)).\
                filter(Episode.id == episode_id).\
                filter(Episode.delete_mark == None).\
                all()

            episode_dict = row2dict(episode)
            utils.process_episode_dict(episode, episode_dict)

            return json_resp({'data': episode_dict})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def delete_episode(self, episode_id):
        try:
            session = SessionManager.Session()
            episode = session.query(Episode).filter(Episode.id == episode_id).one()
            episode.delete_mark = datetime.now()
            session.commit()
            return json_resp({'data': {'delete_delay': self.delete_delay['episode']}})
        finally:
            SessionManager.Session.remove()

    def list_episode(self, page, count, sort_field, sort_order, status):
        try:

            session = SessionManager.Session()
            query_object = session.query(Episode).\
                filter(Episode.delete_mark == None)

            if status is not None:
                query_object = query_object.filter(Episode.status==status)
                # count total rows
                total = session.query(func.count(Episode.id)).filter(Episode.status==status).scalar()
            else:
                total = session.query(func.count(Episode.id)).scalar()

            offset = (page - 1) * count

            if sort_order == 'desc':
                episode_list = query_object.\
                    order_by(desc(getattr(Episode, sort_field))).\
                    offset(offset).\
                    limit(count).\
                    all()
            else:
                episode_list = query_object.\
                    order_by(asc(getattr(Episode, sort_field))).\
                    offset(offset).limit(count).\
                    all()

            episode_dict_list = [row2dict(episode) for episode in episode_list]

            return json_resp({'data': episode_dict_list, 'total': total})
        except Exception as exception:
            raise exception
        finally:
            SessionManager.Session.remove()

    def update_thumbnail(self, episode_id, time):
        try:
            session = SessionManager.Session()
            episode = session.query(Episode).\
                filter(Episode.delete_mark == None).\
                filter(Episode.id == episode_id).one()
            if episode.status != Episode.STATUS_DOWNLOADED:
                raise ClientError('Episode not downloaded', 412)

            torrent_file = session.query(TorrentFile).filter(TorrentFile.episode_id == episode_id).all()[0]

            video_manager.create_episode_thumbnail(episode, torrent_file.file_path, time)

            return json_resp({'msg': 'ok'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def get_episode_video_file_list(self, episode_id):
        try:
            session = SessionManager.Session()
            video_file_list = session.query(VideoFile).\
                filter(VideoFile.episode_id == episode_id).\
                all()

            result = [row2dict(video_file) for video_file in video_file_list]
            return json_resp({'data': result})
        finally:
            SessionManager.Session.remove()

    def add_video_file(self, video_dict):
        try:
            session = SessionManager.Session()
            video_file = VideoFile(bangumi_id=video_dict['bangumi_id'],
                                   episode_id=video_dict['episode_id'],
                                   download_url=video_dict.get('download_url'),
                                   file_path=video_dict.get('file_path'),
                                   file_name=video_dict.get('file_name'),
                                   status=video_dict.get('status', 1),
                                   resolution_w=video_dict.get('resolution_w'),
                                   resolution_h=video_dict.get('resolution_h'),
                                   duration=video_dict.get('duration'),
                                   label=video_dict.get('label'))
            session.add(video_file)
            session.commit()
            video_file_id = str(video_file.id)
            return json_resp({'data': video_file_id})
        finally:
            SessionManager.Session.remove()

    def update_video_file(self, video_file_id, video_dict):
        try:
            session = SessionManager.Session()
            video_file = session.query(VideoFile).filter(VideoFile.id == video_file_id).one()
            video_file.download_url = video_dict.get('download_url')
            video_file.file_path = video_dict.get('file_path')
            video_file.file_name = video_dict.get('file_name')
            video_file.status = video_dict.get('status', 1)
            video_file.resolution_w = video_dict.get('resolution_w')
            video_file.resolution_h = video_dict.get('resolution_h')
            video_file.duration = video_dict.get('duration')
            video_file.label = video_dict.get('label')
            session.commit()
            return json_resp({'msg': 'OK'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def delete_video_file(self, video_file_id):
        try:
            session = SessionManager.Session()
            video_file = session.query(VideoFile).filter(VideoFile.id == video_file_id).one()
            if video_file.file_path is not None and video_file.status == VideoFile.STATUS_DOWNLOADED:
                file_abs_path = u'{0}/{1}/{2}'.format(self.base_path, str(video_file.bangumi_id), video_file.file_path)
                try:
                    os.remove(file_abs_path)
                except Exception as error:
                    logger.warn(error)

            session.delete(video_file)
            session.commit()
            return json_resp({'msg': 'ok'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    # def upload_episode(self, episode_id, file):
    #     try:
    #         filename = secure_filename(file.filename)
    #         session = SessionManager.Session()
    #         (episode, bangumi) = session.query(Episode, Bangumi).\
    #             join(Bangumi).\
    #             filter(Episode.delete_mark == None).\
    #             filter(Episode.id == episode_id).\
    #             one()
    #         file.save(os.path.join(self.base_path, str(episode.bangumi_id), filename))
    #         torrent_file = None
    #         try:
    #             torrent_file = session.query(TorrentFile).filter(TorrentFile.episode_id == episode_id).one()
    #         except NoResultFound:
    #             torrent_file = TorrentFile()
    #             session.add(torrent_file)
    #
    #         torrent_file.torrent_id = str(-1)
    #         torrent_file.episode_id = episode_id
    #         torrent_file.file_path = filename
    #
    #         episode.update_time = datetime.now()
    #         episode.status = Episode.STATUS_DOWNLOADED
    #
    #         session.commit()
    #
    #         return json_resp({'msg': 'ok'})
    #     except NoResultFound:
    #         raise ClientError(ClientError.INVALID_REQUEST)
    #     except Exception as error:
    #         raise error
    #     finally:
    #         SessionManager.Session.remove()


admin_service = AdminService()
