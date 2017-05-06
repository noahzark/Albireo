from domain.base import Base
from sqlalchemy import Column, String, TEXT, Integer, TIMESTAMP, BOOLEAN
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime


class User(Base):
    __tablename__ = 'users'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, unique=True, nullable=False)
    password = Column(TEXT, nullable=False)
    # default user level is 0
    # when user confirm their email, promote to level 1
    level = Column(Integer, nullable=False, default=0)

    email = Column(String(512), nullable=True)
    email_confirmed = Column(BOOLEAN, nullable=False, default=False)

    register_time = Column(TIMESTAMP, nullable=False, default=datetime.now)
    update_time = Column(TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now)

    # predefined user level
    LEVEL_DEFAULT = 0
    LEVEL_USER = 1
    LEVEL_ADMIN = 2
    LEVEL_SUPER_USER = 3

