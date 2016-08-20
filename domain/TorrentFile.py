from domain.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4


class TorrentFile(Base):
    __tablename__ = 'torrentfile'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    episode_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('episodes.id'), nullable=False)
    torrent_id = Column(String, nullable=False)
    file_path = Column(TEXT, nullable=True)

    episode = relationship('Episode', back_populates='torrent_files')

