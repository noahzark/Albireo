from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TEXT, Integer
from uuid import uuid4

from sqlalchemy.orm import relationship

from domain.base import Base


class WebHook(Base):
    __tablename__ = 'web_hook'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(TEXT, nullable=False)
    description = Column(TEXT, nullable=True)
    url = Column(TEXT, nullable=False)
    status = Column(Integer, nullable=False)

    web_hook_tokens = relationship('WebHookToken', back_populates='web_hook')

    STATUS_IS_ALIVE = 1
    STATUS_HAS_ERROR = 2
    STATUS_IS_DEAD = 3
