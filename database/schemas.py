import uuid
from typing import Optional
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class LeaderBoardUpdate(schemas.BaseModel):
    pass
