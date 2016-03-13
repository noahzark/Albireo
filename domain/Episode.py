from sqlalchemy import Column, Integer, TEXT, DATE, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship

Base = declarative_base()


class Episode(Base):
    __tablename__ = 'episodes'

    id = Column(postgresql.UUID, primary_key=True)
    bangumi_id = Column(postgresql.UUID, ForeignKey('bangumi.id'))
    bgm_eps_id = Column(Integer)
    episode_no = Column(Integer)
    name = Column(TEXT)
    name_cn = Column(TEXT, nullable=True)
    duration = Column(Integer, nullable=True)
    air_date = Column(DATE, nullable=True)
    status = Column(Integer)

    bangumi = relationship('Bangumi', back_populates='episodes')

    STATUS_NOT_DOWNLOADED = 0
    STATUS_DOWNLOADING = 1
    STATUS_DOWNLOADED = 2
