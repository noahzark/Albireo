from domain.base import Base
from sqlalchemy import Column, Integer
from sqlalchemy.dialects import postgresql
from uuid import uuid4


class Favorites(Base):
    __tablename__ = 'favorites'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(postgresql.UUID(as_uuid=True), nullable=False)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), nullable=False)

    status = Column(Integer, nullable=False, default=0)

    # status
    WISH = 0
    WATCHED = 1
    WATCHING = 2
    PAUSE = 3
    ABANDONED = 4
