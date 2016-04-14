from sqlalchemy import Column, Integer, TEXT, DATE, ForeignKey, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime

Base = declarative_base()


class TorrentFile(Base):
    __tablename__ = 'torrentfile'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('episodes.id'))
    torrent_id = Column(String)
    file_path = Column(TEXT)

    episode = relationship('Episode', back_populates='torrent_files')


class Episode(Base):
    __tablename__ = 'episodes'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('bangumi.id'))
    bgm_eps_id = Column(Integer)
    episode_no = Column(Integer)
    name = Column(TEXT)
    name_cn = Column(TEXT, nullable=True)
    duration = Column(String, nullable=True)
    airdate = Column(DATE, nullable=True)
    status = Column(Integer)
    torrent_id = Column(String, nullable=True)
    create_time = Column(TIMESTAMP, default=datetime.now())
    update_time = Column(TIMESTAMP, default=datetime.now())

    bangumi = relationship('Bangumi', back_populates='episodes')

    torrent_files = relationship('TorrentFile', order_by=TorrentFile.episode_id, back_populates='episode',
                                 cascade='all, delete, delete-orphan')

    STATUS_NOT_DOWNLOADED = 0
    STATUS_DOWNLOADING = 1
    STATUS_DOWNLOADED = 2



class Bangumi(Base):
    __tablename__ = 'bangumi'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    bgm_id = Column(Integer)
    name = Column(TEXT)
    name_cn = Column(TEXT)
    eps = Column(Integer)
    summary = Column(TEXT)
    image = Column(TEXT)
    air_date = Column(DATE)
    air_weekday = Column(Integer)
    rss = Column(TEXT, nullable=True)
    eps_regex = Column(TEXT, nullable=True)
    status = Column(Integer)
    create_time = Column(TIMESTAMP, default=datetime.now())
    update_time = Column(TIMESTAMP, default=datetime.now())

    episodes = relationship('Episode', order_by=Episode.episode_no, back_populates='bangumi',
                            cascade='all, delete, delete-orphan')

    # constant of bangumi status
    # A pending bangumi is not started to show on tv yet
    STATUS_PENDING = 0
    # An on air bangumi is currently on air on tv. And not finished yet
    STATUS_ON_AIR = 1
    # A finished bangumi will no longer need to scanned
    STATUS_FINISHED = 2
