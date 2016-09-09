from domain.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, String
from sqlalchemy.dialects import postgresql
from uuid import uuid4


class Feed(Base):
    __tablename__ = 'feed'

    episode_id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), nullable=False)
    download_url = Column(TEXT, nullable=False)
    torrent_file_id = Column(postgresql.UUID(as_uuid=True), nullable=True)
