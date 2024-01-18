from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, conint


class UserCreateSchema(BaseModel):
    email: EmailStr
    password: str


class UserOutSchema(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateSchema(BaseModel):
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str


class TokenDataSchema(BaseModel):
    id: Optional[int] = None


class PostBaseSchema(BaseModel):
    title: str
    content: str
    published: bool = True


class PostCreateSchema(PostBaseSchema):
    pass


class PostSchema(PostBaseSchema):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOutSchema
    votes: Optional[int] = 0

    class Config:
        from_attributes = True


class VoteBaseSchema(BaseModel):
    post_id: int
    dir: conint(le=1)
