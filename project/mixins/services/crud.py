from typing import Any, Type

from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from database import Base


class CRUDOperationsService:
    """
    Service class for common CRUD operations with objects.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def get_object(
            self,
            available_db_data: Select,
            model_for_lookup: Type[Base],
            search_value: Any,
            lookup_kwarg: str = 'id'
    ) -> Any:
        """
        Must return object from available bd data using lookup_kwarg.
        """
        get_object_query = available_db_data.where(getattr(model_for_lookup, lookup_kwarg, None) == search_value)
        obj = await self.db_session.execute(get_object_query)
        return obj.scalar()

    async def update_object_in_database(self, object_to_update: Base, **data_for_update) -> Base:
        """
        Updates existing object in database with given data for update.
        """
        for attr, value in data_for_update.items():
            setattr(object_to_update, attr, value)
        return await self.create_object_in_database(object_to_update)

    async def create_object_in_database(self, object_to_create: Base) -> Base:
        """
        Creates the given object_to_create in database (updates if it's already an existing object).
        """
        self.db_session.add(object_to_create)
        await self.db_session.commit()
        await self.db_session.refresh(object_to_create)
        return object_to_create