# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound

from domain.Episode import Episode
from domain.Bangumi import Bangumi
from domain.Favorites import Favorites
from domain.WatchProgress import WatchProgress
from domain.TorrentFile import TorrentFile
from datetime import datetime, timedelta
from utils.SessionManager import SessionManager
from utils.exceptions import ClientError
from utils.http import json_resp
from utils.db import row2dict
from sqlalchemy.sql.expression import or_, desc, asc
from sqlalchemy.sql import select, func, distinct
from sqlalchemy.orm import joinedload
import json
from service.common import utils

class BangumiService:

    def recent_update(self, days):

        current = datetime.now()

        # from one week ago
        start_time = current - timedelta(days=days)

        session = SessionManager.Session()
        try:
            result = session.query(Episode, Bangumi).\
                join(Bangumi).\
                filter(Episode.status == Episode.STATUS_DOWNLOADED).\
                filter(Episode.update_time >= start_time).\
                filter(Episode.update_time <= current).\
                order_by(desc(Episode.update_time))

            episode_list = []

            for eps, bgm in result:
                episode = row2dict(eps)
                episode['thumbnail'] = utils.generate_thumbnail_link(eps, bgm)
                episode['bangumi'] = row2dict(bgm)
                episode['bangumi']['cover'] = utils.generate_cover_link(bgm)
                episode_list.append(episode)

            return json_resp({'data': episode_list})
        except Exception as error:
            raise error
        finally:
            SessionManager.Session.remove()


    def episode_detail(self, episode_id, user_id):
        session = SessionManager.Session()
        try:
            (episode, bangumi, watch_progress) = session.query(Episode, Bangumi, WatchProgress).\
                join(Bangumi).\
                join(WatchProgress).\
                filter(Episode.id == episode_id).\
                filter(WatchProgress.user_id == user_id).\
                one()
            episode_dict = row2dict(episode)
            episode_dict['bangumi'] = row2dict(bangumi)
            episode_dict['bangumi']['cover'] = utils.generate_cover_link(bangumi)
            episode_dict['thumbnail'] = utils.generate_thumbnail_link(episode, bangumi)
            episode_dict['watch_progress'] = row2dict(watch_progress)

            if episode.status == Episode.STATUS_DOWNLOADED:
                episode_dict['videos'] = []
                torrent_file_cur = session.query(TorrentFile).filter(TorrentFile.episode_id == episode_id)
                for torrent_file in torrent_file_cur:
                    episode_dict['videos'].append(utils.generate_video_link(str(bangumi.id), torrent_file.file_path))

            return json_resp(episode_dict)
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def on_air_bangumi(self, user_id):
        session = SessionManager.Session()
        current_day = datetime.today()
        start_time = datetime(current_day.year, current_day.month, 1)
        if current_day.month == 12:
            next_year = current_day.year + 1
            next_month = 1
        else:
            next_year = current_day.year
            next_month = current_day.month + 1
        end_time = datetime(next_year, next_month, 1)

        try:
            result = session.query(distinct(Episode.bangumi_id), Bangumi, Favorites).\
                join(Bangumi, Favorites).\
                filter(Episode.airdate >= start_time).\
                filter(Episode.airdate <= end_time).\
                filter(Favorites.user_id == user_id)

            bangumi_list = []
            for bangumi_id, bangumi, favorite in result:
                bangumi_dict = row2dict(bangumi)
                bangumi_dict['cover'] = utils.generate_cover_link(bangumi)
                bangumi_dict['favorite_status'] = favorite.status
                bangumi_list.append(bangumi_dict)

            return json_resp({'data': bangumi_list})
        except Exception as error:
            raise error
        finally:
            SessionManager.Session.remove()

    def get_bangumi(self, id, user_id):
        try:
            session = SessionManager.Session()

            (bangumi, favorite) = session.query(Bangumi, Favorites).\
                join(Favorites).\
                options(joinedload(Bangumi.episodes)).\
                filter(Bangumi.id == id).\
                filter(Favorites.user_id == user_id).\
                one()

            watch_progress_list = session.query(WatchProgress).\
                filter(WatchProgress.bangumi_id == bangumi.id).\
                filter(WatchProgress.user_id == user_id).\
                all()

            episodes = []

            watch_progress_hash_table = {}
            for watch_progress in watch_progress_list:
                watch_progress_dict = row2dict(watch_progress)
                watch_progress_hash_table[watch_progress.episode_id] = watch_progress_dict

            for episode in bangumi.episodes:
                eps = row2dict(episode)
                eps['thumbnail'] = utils.generate_thumbnail_link(episode, bangumi)
                if episode.id in watch_progress_hash_table:
                    eps['watch_progress'] = watch_progress_hash_table[episode.id]
                episodes.append(eps)

            bangumi_dict = row2dict(bangumi)

            bangumi_dict['favorite_status'] = favorite.status

            bangumi_dict['episodes'] = episodes

            bangumi_dict['cover'] = utils.generate_cover_link(bangumi)

            return json_resp({'data': bangumi_dict})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

bangumi_service = BangumiService()
