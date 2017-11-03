from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TEXT, Integer
from uuid import uuid4

from domain.base import Base


class Task(Base):
    __tablename__ = 'task'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(Integer, nullable=False)
    content = Column(TEXT, nullable=True)
    status = Column(Integer, nullable=True)

    # type
    TYPE_BANGUMI_DELETE = 1
    TYPE_EPISODE_DELETE = 2

    # status
    STATUS_IN_PROGRESS = 1
    STATUS_COMPLETE = 2
