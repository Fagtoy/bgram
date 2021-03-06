from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from accounts.api.filters.users import UsersFilterSet
from accounts.api.pagination.users import UsersPaginationDatabaseObjectsRetrieverStrategy
from accounts.database.repository.users import IUsersDatabaseRepository
from accounts.models import User, UserPhoto
from accounts.services.users import UsersRetrieveService, UsersCreateUpdateService, IUsersRetrieveService
from core.database.repository import SQLAlchemyDatabaseRepository
from core.filters import FilterSet
from core.pagination import DefaultPaginationClass
from core.services.files import FilesService


class UsersDependenciesProvider:
    @staticmethod
    async def get_users_db_repository(db_session: AsyncSession = Depends()):
        return SQLAlchemyDatabaseRepository(User, db_session)

    @staticmethod
    async def get_users_retrieve_service(db_repository: IUsersDatabaseRepository = Depends()):
        return UsersRetrieveService(db_repository)

    @staticmethod
    async def get_users_create_update_service(db_repository: IUsersDatabaseRepository = Depends()):
        return UsersCreateUpdateService(db_repository)

    @staticmethod
    async def get_user_photos_service(db_repository: IUsersDatabaseRepository = Depends()):
        return FilesService(db_repository, UserPhoto)

    @staticmethod
    async def get_users_filterset(request: Request) -> FilterSet:
        return UsersFilterSet(request=request)

    @staticmethod
    async def get_users_paginator(
            request: Request,
            users_retrieve_service: IUsersRetrieveService = Depends(),
    ) -> DefaultPaginationClass:
        users_db_objects_retriever_strategy = UsersPaginationDatabaseObjectsRetrieverStrategy(users_retrieve_service)
        return DefaultPaginationClass(request, users_db_objects_retriever_strategy)
