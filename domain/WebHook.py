from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TEXT, Integer, TIMESTAMP
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import relationship

from domain.base import Base


class WebHook(Base):
    __tablename__ = 'web_hook'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(TEXT, nullable=False)
    description = Column(TEXT, nullable=True)
    url = Column(TEXT, nullable=False)
    status = Column(Integer, nullable=False, default=4)
    consecutive_failure_count = Column(Integer, nullable=False, default=0)
    register_time = Column(TIMESTAMP, nullable=False, default=datetime.now)

    web_hook_tokens = relationship('WebHookToken', back_populates='web_hook')

    STATUS_IS_ALIVE = 1
    STATUS_HAS_ERROR = 2
    STATUS_IS_DEAD = 3
    STATUS_INITIAL = 4
