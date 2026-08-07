from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr = Field(max_length=120)


class UpdateUser(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)
    img_file: str | None = Field(default=None, max_length=255)


class CreateUser(UserBase):
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    img_file: str | None
    img_path: str


class UserPrivateResponse(UserResponse):
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class PostBase(BaseModel):
    title: str = Field(max_length=100, min_length=6)
    body: str = Field(min_length=2)
    tags: list[str] = Field(default_factory=list)


class CreatePost(PostBase):
    user_id: int  # TEMPORARY


class UpdatePost(BaseModel):
    title: str | None = Field(default=None, max_length=100, min_length=6)
    body: str | None = Field(default=None, min_length=2)
    tags: list[str] | None = Field(default=None)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author: UserResponse
    slug: str
    date_posted: datetime
