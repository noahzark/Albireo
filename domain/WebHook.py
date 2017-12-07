from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TEXT, Integer, TIMESTAMP
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import relationship

from domain.base import Base
from domain.User import User
import json
import logging

logger = logging.getLogger(__name__)


class WebHook(Base):
    __tablename__ = 'web_hook'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(TEXT, nullable=False, unique=True)
    description = Column(TEXT, nullable=True)
    url = Column(TEXT, nullable=False)
    status = Column(Integer, nullable=False, default=4)
    consecutive_failure_count = Column(Integer, nullable=False, default=0)
    register_time = Column(TIMESTAMP, nullable=False, default=datetime.now)
    created_by_uid = Column(postgresql.UUID(as_uuid=True), nullable=True)
    shared_secret = Column(TEXT, nullable=False)
    permissions = Column(TEXT, nullable=False, default='[]')

    web_hook_tokens = relationship('WebHookToken', back_populates='web_hook')

    created_by = relationship(User,
                              foreign_keys=[created_by_uid],
                              primaryjoin='WebHook.created_by_uid==User.id')

    def has_permission(self, permission):
        try:
            permisson_list = json.loads(self.permissions)
            if permission in permisson_list:
                return True
            else:
                return False
        except Exception as error:
            logger.error(error)
            return False

    STATUS_IS_ALIVE = 1
    STATUS_HAS_ERROR = 2
    STATUS_IS_DEAD = 3
    STATUS_INITIAL = 4

    PERMISSION_FAVORITE = 'PERM_FAVORITE'
    PERMISSION_EMAIL = 'PERM_EMAIL'
