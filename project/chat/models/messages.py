from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from mixins.models import DateTimeABC, PhotoABC

__all__ = ['Message', 'MessagePhoto']


class Message(DateTimeABC):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    is_read = Column(Boolean, default=False)
    is_edited = Column(Boolean, default=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))

    author = relationship('User', back_populates='messages')
    photos = relationship('MessagePhoto', back_populates='message')


class MessagePhoto(PhotoABC):
    __tablename__ = 'message_photos'

    message_id = Column(Integer, ForeignKey('chat_rooms.id'))

    message = relationship('Message', back_populates='photos', cascade='all, delete')

    @property
    def folder_to_save(self) -> str:
        """
        Returns path to directory where to save a file.
        """
        return f'message/{self.message_id}/'
