from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.engine.result import ChunkedIteratorResult
from sqlalchemy.orm import Session

from accounts.models import User, UserPhoto
from accounts.utils.user import get_hashed_password
from mixins import utils as mixins_utils


async def create_user(nickname: str, email: str, password: str, db_session: Session, **kwargs) -> User:
    user = User(nickname=nickname, email=email, password=get_hashed_password(password), **kwargs)
    await mixins_utils.create_object_in_database(user, db_session)
    return user


async def get_users(
        db_session: Session,
        available_db_data: Optional[ChunkedIteratorResult] = select(User)
) -> List[User]:
    users = await db_session.execute(available_db_data)
    return users.unique().scalars().all()


async def get_user(
        search_value: int,
        db_session: Session,
        lookup_kwarg: Optional[str] = 'id',
        available_db_data: Optional[ChunkedIteratorResult] = select(User)
) -> User:
    return await mixins_utils.get_object(
        available_db_data, User, search_value, db_session=db_session, lookup_kwarg=lookup_kwarg
    )


async def update_user(user: User, db_session: Session, **data_for_update) -> User:
    for attr, value in data_for_update.items():
        setattr(user, attr, value)
    await mixins_utils.create_object_in_database(user, db_session)
    return user


async def create_user_photo(user_id: int, file: UploadFile, db_session: Session) -> UserPhoto:
    return await mixins_utils.create_object_file(UserPhoto, file, db_session=db_session, user_id=user_id)