from domain.base import Base
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4


class Favorites(Base):
    __tablename__ = 'favorites'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(postgresql.UUID(as_uuid=True), nullable=False)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('bangumi.id'), nullable=False)

    status = Column(Integer, nullable=False, default=0)

    bangumi = relationship('Bangumi', uselist=False, back_populates='favorite')

    # status
    WISH = 1
    WATCHED = 2
    WATCHING = 3
    PAUSE = 4
    ABANDONED = 5
