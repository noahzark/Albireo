from sqlalchemy import and_
from datetime import datetime
from utils.SessionManager import SessionManager
from utils.http import json_resp
from domain.Favorites import Favorites
from domain.WatchProgress import WatchProgress

import logging

logger = logging.getLogger(__name__)


class WatchService:

    def favorite_bangumi(self, bangumi_id, user_id, status):
        session = SessionManager.Session()
        try:
            favorite = session.query(Favorites).filter(and_(Favorites.bangumi_id == bangumi_id, Favorites.user_id == user_id)).first()
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
            watch_progress = session.query(WatchProgress).filter(and_(WatchProgress.bangumi_id == bangumi_id, WatchProgress.episode_id == episode_id, WatchProgress.user_id == user_id)).first()
            if watch_progress is None:
                watch_progress = WatchProgress(bangumi_id=bangumi_id, episode_id=episode_id, user_id=user_id, watch_status=watch_status)
                session.add(watch_progress)
            else:
                watch_progress.watch_status = watch_status

            session.commit()
            return json_resp({'message': 'ok', 'status': 0})
        finally:
            SessionManager.Session.remove()

    def episode_history(self, bangumi_id, episode_id, user_id, last_watch_position, is_finished):
        last_watch_time = datetime.now()
        watch_status = WatchProgress.WATCHED if is_finished else WatchProgress.WATCHING

        session = SessionManager.Session()
        try:
            watch_progress = session.query(WatchProgress).filter(and_(WatchProgress.bangumi_id == bangumi_id, WatchProgress.episode_id == episode_id, WatchProgress.user_id == user_id)).first()
            if watch_progress is None:
                watch_progress = WatchProgress(bangumi_id=bangumi_id, episode_id=episode_id, user_id=user_id, watch_status=watch_status, last_play_position=last_watch_position, last_play_time=last_watch_time)
                session.add(watch_progress)
            else:
                watch_progress.watch_status = watch_status
                watch_progress.last_watch_time = last_watch_time
                watch_progress.last_watch_position = last_watch_position

            session.commit()
            return json_resp({'message': 'ok', 'status': 0})
        finally:
            SessionManager.Session.remove()

watch_service = WatchService()
