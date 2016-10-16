from domain.base import Base
from domain.Episode import Episode
from sqlalchemy import Column, Integer, TEXT, DATE, TIMESTAMP
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime


class Bangumi(Base):
    __tablename__ = 'bangumi'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    bgm_id = Column(Integer, nullable=False)
    name = Column(TEXT , nullable=False)
    name_cn = Column(TEXT, nullable=False)
    eps = Column(Integer, nullable=False)
    summary = Column(TEXT, nullable=False)
    image = Column(TEXT, nullable=False)
    air_date = Column(DATE, nullable=False)
    air_weekday = Column(Integer, nullable=False)
    rss = Column(TEXT, nullable=True)
    dmhy = Column(TEXT, nullable=True)
    eps_no_offset = Column(Integer, nullable=True)
    acg_rip = Column(TEXT, nullable=True)
    eps_regex = Column(TEXT, nullable=True)
    status = Column(Integer, nullable=False)
    create_time = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    update_time = Column(TIMESTAMP, default=datetime.now(), nullable=False)

    episodes = relationship('Episode', order_by=Episode.episode_no, back_populates='bangumi',
                            cascade='all, delete, delete-orphan')

    # constant of bangumi status
    # A pending bangumi is not started to show on tv yet
    STATUS_PENDING = 0
    # An on air bangumi is currently on air on tv. And not finished yet
    STATUS_ON_AIR = 1
    # A finished bangumi will no longer need to scanned
    STATUS_FINISHED = 2
