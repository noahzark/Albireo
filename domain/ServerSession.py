from base import Base
from sqlalchemy import TEXT, Column, DateTime, LargeBinary
from sqlalchemy.dialects import postgresql
from uuid import uuid4

class ServerSession(Base):
    __tablename__ = 'server_session'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(TEXT, unique=True)
    data = Column(LargeBinary)
    expiry = Column(DateTime)
