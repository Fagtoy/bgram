from abc import ABC
from typing import Optional, Tuple

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import Select

from chat.events.messages import message_created_event, message_updated_event, messages_deleted_event
from chat.models import Message, MessagePhoto
from core.dependencies import EventPublisher
from core.database.repository import BaseDatabaseRepository
from core.services.files import FilesService


class IMessagesRetrieveService(ABC):
    async def get_one_message(self, *args, db_query: Optional[Select] = None) -> Message:
        pass

    async def get_many_messages(self, *args, db_query: Optional[Select] = None) -> list[Message]:
        pass

    async def count_messages(self, *args, db_query: Optional[Select] = None) -> int:
        pass


class MessagesRetrieveService(IMessagesRetrieveService):
    def __init__(self, db_repository: BaseDatabaseRepository):
        self.db_repository = db_repository

    async def get_one_message(self, *args, db_query: Optional[Select] = None) -> Message:
        if db_query is not None:
            self.db_repository.db_query = db_query
        return await self.db_repository.get_one(*args)

    async def get_many_messages(self, *args, db_query: Optional[Select] = None) -> list[Message]:
        if db_query is not None:
            self.db_repository.db_query = db_query
        return await self.db_repository.get_many(*args)

    async def count_messages(self, *args, db_query: Optional[Select] = None) -> int:
        if db_query is not None:
            self.db_repository.db_query = db_query
        return await self.db_repository.count(*args)


class IMessagesCreateUpdateDeleteService(ABC):
    async def create_message(self, *args, **kwargs) -> Message:
        pass

    async def update_message(self, *args, **kwargs) -> Message:
        pass

    async def delete_messages(self, *args) -> tuple[int]:
        pass


class MessagesCreateUpdateDeleteService(IMessagesCreateUpdateDeleteService):
    def __init__(
            self,
            db_repository: BaseDatabaseRepository,
            chat_room_id: Optional[int] = None,
            event_publisher: Optional[EventPublisher] = None,
            files_service: Optional[FilesService] = None,
    ):
        self.db_repository = db_repository
        self.chat_room_id = chat_room_id
        self.event_publisher = event_publisher
        self.files_service = files_service

    async def create_message(
            self,
            text: str,
            files: Optional[Tuple[UploadFile]] = None,
            author_id: Optional[int] = None,
            **kwargs
    ) -> Message:
        message = Message(chat_room_id=self.chat_room_id, text=text, author_id=author_id, **kwargs)
        created_message = await self.db_repository.create(message)
        await self.db_repository.commit()
        await self.db_repository.refresh(created_message)
        message_id = created_message.id
        if files:
            for file in files:
                await self.files_service.create_object_file(file, message_id=message_id)
        self.db_repository.db_query = select(Message).options(joinedload(Message.author), joinedload(Message.photos))
        created_message = await self.db_repository.get_one(Message.id == message_id)
        await message_created_event(self.event_publisher, created_message, self.db_repository)
        return created_message

    async def update_message(self, message: Message, **kwargs) -> Message:
        if not message.is_edited:
            kwargs['is_edited'] = True
        updated_message = await self.db_repository.update_object(message, **kwargs)
        await self.db_repository.commit()
        await self.db_repository.refresh(updated_message)
        await message_updated_event(self.event_publisher, updated_message, self.db_repository)
        return updated_message

    async def delete_messages(self, message_ids: tuple[int]) -> tuple[int]:
        await self.db_repository.delete(Message.id.in_(message_ids))
        await self.db_repository.commit()
        await messages_deleted_event(self.event_publisher, self.chat_room_id, message_ids)
        return message_ids


class IMessageFilesRetrieveService(ABC):
    async def get_one_message_file(self, *args, db_query: Optional[Select] = None) -> Message:
        pass


class MessageFilesRetrieveService(IMessageFilesRetrieveService):
    def __init__(self, db_repository: BaseDatabaseRepository):
        self.db_repository = db_repository

    async def get_one_message_file(self, *args, db_query: Optional[Select] = None) -> Message:
        if db_query is not None:
            self.db_repository.db_query = db_query
        return await self.db_repository.get_one(*args)


class IMessageFilesService(ABC):
    async def change_message_file(self, replacement_file: UploadFile) -> MessagePhoto:
        pass

    async def delete_message_file(self):
        pass


class MessageFilesService(IMessageFilesService):
    def __init__(self, message_file: MessagePhoto, files_service: FilesService, event_publisher: EventPublisher):
        self.message_file = message_file
        self.message = message_file.message
        self.event_publisher = event_publisher
        self.files_service = files_service

    async def change_message_file(self, replacement_file: UploadFile) -> MessagePhoto:
        new_message_file: MessagePhoto = await self.files_service.change_file(self.message_file.id, replacement_file)
        await message_updated_event(self.event_publisher, self.message)
        return new_message_file

    async def delete_message_file(self):
        await self.files_service.delete_file_object(self.message_file.id)
        await message_updated_event(self.event_publisher, self.message)
