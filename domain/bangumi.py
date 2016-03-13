from sqlalchemy import Column, Integer, TEXT, DATE
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from domain.Episode import Episode

Base = declarative_base()


class Bangumi(Base):
    __tablename__ = 'bangumi'

    id = Column(postgresql.UUID, primary_key=True)
    bgm_id = Column(Integer)
    name = Column(TEXT)
    name_cn = Column(TEXT)
    eps = Column(Integer)
    summary = Column(TEXT)
    image = Column(TEXT)
    air_date = Column(DATE)
    air_weekday = Column(Integer)
    rss = Column(TEXT)
    eps_regex = Column(TEXT)
    status = Column(Integer)

    episodes = relationship('Episode', order_by=Episode.id, back_populates='bangumi')

    # constant of bangumi status
    # A pending bangumi is not started to show on tv yet
    STATUS_PENDING = 0
    # An on air bangumi is currently on air on tv. And not finished yet
    STATUS_ON_AIR = 1
    # A finished bangumi will no longer need to scanned
    STATUS_FINISHED = 2