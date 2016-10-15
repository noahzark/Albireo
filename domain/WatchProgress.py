from domain.base import Base
from sqlalchemy import Column, Integer, TIMESTAMP
from sqlalchemy.dialects import postgresql
from uuid import uuid4
from datetime import datetime


class WatchProgress(Base):
    __tablename__ = 'watch_progress'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(postgresql.UUID(as_uuid=True), nullable=False)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), nullable=False)
    episode_id = Column(postgresql.UUID(as_uuid=True), nullable=False)

    watch_status = Column(Integer, nullable=False, default=0)

    # last watched position in milliseconds, only usable when watch_status is WATCHING
    last_watch_position = Column(Integer, nullable=True)

    last_watch_time = Column(TIMESTAMP, nullable=True)

    # some status is for favorites purpose
    NOT_WATCHED = 0
    WATCHING = 1
    WATCHED = 2
    WISH = 3
    ABANDONED = 4
