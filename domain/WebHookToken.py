from sqlalchemy.dialects import postgresql
from sqlalchemy import Column, TEXT, ForeignKey
from sqlalchemy.orm import relationship

from domain.base import Base


class WebHookToken(Base):
    __tablename__ = 'web_hook_token'

    token_id = Column(TEXT, nullable=False)
    user_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, primary_key=True)
    web_hook_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('web_hook.id'), nullable=False, primary_key=True)

    web_hook = relationship('WebHook', back_populates='web_hook_tokens')
