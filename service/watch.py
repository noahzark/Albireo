from datetime import datetime
from sqlalchemy.sql import func
from utils.SessionManager import SessionManager
from utils.http import json_resp
from utils.db import row2dict
from domain.Favorites import Favorites
from domain.WatchProgress import WatchProgress
from domain.Bangumi import Bangumi
from domain.Episode import Episode

import logging

logger = logging.getLogger(__name__)


class WatchService:

    def favorite_bangumi(self, bangumi_id, user_id, status):
        session = SessionManager.Session()
        try:
            favorite = session.query(Favorites).\
                filter(Favorites.bangumi_id == bangumi_id).\
                filter(Favorites.user_id == user_id).\
                first()
            if not favorite:
                favorite = Favorites(bangumi_id=bangumi_id, user_id=user_id, status=status)
                session.add(favorite)
            else:
                favorite.status = status

            session.commit()
            return json_resp({'message': 'ok', 'status': 0})
        finally:
            SessionManager.Session.remove()

    def favorite_episode(self, bangumi_id, episode_id, user_id, watch_status):
        session = SessionManager.Session()
        try:
            watch_progress = session.query(WatchProgress).\
                filter(WatchProgress.bangumi_id == bangumi_id).\
                filter(WatchProgress.episode_id == episode_id).\
                filter(WatchProgress.user_id == user_id).\
                first()
            if watch_progress is None:
                watch_progress = WatchProgress(bangumi_id=bangumi_id,
                                               episode_id=episode_id,
                                               user_id=user_id,
                                               watch_status=watch_status)
                session.add(watch_progress)
            else:
                watch_progress.watch_status = watch_status

            session.commit()
            return json_resp({'message': 'ok', 'status': 0})
        finally:
            SessionManager.Session.remove()

    def episode_history(self, bangumi_id, episode_id, user_id, last_watch_position, percentage, is_finished):
        last_watch_time = datetime.now()
        watch_status = WatchProgress.WATCHED if is_finished else WatchProgress.WATCHING

        session = SessionManager.Session()
        try:
            watch_progress = session.query(WatchProgress).\
                filter(WatchProgress.bangumi_id == bangumi_id).\
                filter(WatchProgress.episode_id == episode_id).\
                filter(WatchProgress.user_id == user_id).\
                first()
            if watch_progress is None:
                watch_progress = WatchProgress(bangumi_id=bangumi_id,
                                               episode_id=episode_id,
                                               user_id=user_id,
                                               watch_status=watch_status,
                                               last_watch_position=last_watch_position,
                                               last_watch_time=last_watch_time,
                                               percentage=0)
                session.add(watch_progress)
            else:
                watch_progress.watch_status = watch_status
                watch_progress.last_watch_time = last_watch_time
                watch_progress.last_watch_position = last_watch_position
                watch_progress.percentage = percentage

            session.commit()
            return json_resp({'message': 'ok', 'status': 0})
        finally:
            SessionManager.Session.remove()

    def my_favorites(self, user_id, status=None):
        session = SessionManager.Session()
        try:
            q = session.query(Favorites, Bangumi).\
                join(Bangumi).\
                filter(Favorites.user_id == user_id)

            if status is None:
                result = q.all()
            else:
                result = q.filter(Favorites.status == status).all()

            bangumi_id_list = [bangumi.id for favorite, bangumi in result]

            # subquery for watch_progress
            watch_progress = session.query(WatchProgress.episode_id).\
                filter(WatchProgress.user_id == user_id).\
                filter(WatchProgress.bangumi_id.in_(bangumi_id_list))

            episode_count = session.query(func.count(Episode.id), Episode.bangumi_id).\
                filter(Episode.status == Episode.STATUS_DOWNLOADED).\
                filter(Episode.bangumi_id.in_(bangumi_id_list)).\
                filter(~Episode.id.in_(watch_progress)).\
                group_by(Episode.bangumi_id).\
                all()

            logger.debug(episode_count)
            bangumi_dict_list = []

            for fav, bgm in result:
                bangumi_dict = row2dict(bgm)
                bangumi_dict['favorite_status'] = fav.status
                for unwatched_count, bangumi_id in episode_count:
                    if bangumi_id == bgm.id:
                        bangumi_dict['unwatched_count'] = unwatched_count
                        break
                bangumi_dict_list.append(bangumi_dict)

            return json_resp({'data': bangumi_dict_list, 'status': 0})

        finally:
            SessionManager.Session.remove()

watch_service = WatchService()
