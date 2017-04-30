from domain.base import Base
from sqlalchemy import Column, String, TEXT, Integer
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4


class User(Base):
    __tablename__ = 'users'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, unique=True, nullable=False)
    password = Column(TEXT, nullable=False)
    # default user level is 0
    level = Column(Integer, nullable=False)

    email = Column(String(512), nullable=True)

    # predefined user level
    LEVEL_DEFAULT = 0
    LEVEL_USER = 1
    LEVEL_ADMIN = 2
    LEVEL_SUPER_USER = 3
