from sqlalchemy import and_

from utils.SessionManager import SessionManager
from domain.Favorites import Favorites
from domain.WatchProgress import WatchProgress


class WatchService:

    def __init__(self):
        pass

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
        finally:
            SessionManager.Session.remove()

    def favorite_episode(self, bangumi_id, episode_id, user_id, status):
        session = SessionManager.Session()
        try:
            watch_progress = session.query(WatchProgress).filter(and_(WatchProgress.bangumi_id == bangumi_id, WatchProgress.episode_id == episode_id, WatchProgress.user_id == user_id)).first()
            if not watch_progress:
                watch_progress = WatchProgress(bangumi_id=bangumi_id, episode_id=episode_id, user_id=user_id, status=status)
                session.add(watch_progress)
            else:
                watch_progress.status = status

            session.commit()
        finally:
            SessionManager.Session.remove()

watch_service = WatchService()
