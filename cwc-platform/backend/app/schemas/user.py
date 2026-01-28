from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    name: str | None = None


class UserCreate(UserBase):
    google_id: str | None = None
    avatar_url: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    id: str
    avatar_url: str | None = None
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    google_id: str | None = None
