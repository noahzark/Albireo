from domain.base import Base
from sqlalchemy import Column, String, TEXT, Integer
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4


class User(Base):
    __tablename__ = 'user'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)
    password = Column(TEXT)
    # default user level is 0
    level = Column(Integer)