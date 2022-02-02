from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, validator

from core.config import settings


class FilesSchema(BaseModel):
    id: int
    created_at: datetime
    file_path: str

    class Config:
        orm_mode = True

    @validator('file_path')
    def file_path_with_media_url(cls, value) -> str:
        return f'{settings.HOST_DOMAIN}/{settings.MEDIA_URL}/{value}'


class PhotosFieldSchemaMixin(BaseModel):
    photos: List[FilesSchema]


class PaginatedResponseSchemaMixin(BaseModel):
    total: int
    count: int
    next: Optional[str]
    previous: Optional[str]
