from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserRole(str, Enum):
    guest = "guest"
    admin = "admin"
    user = "user"
    artist = "artist"

    all = [admin, user, artist, guest]


class User(BaseModel):
    _id: Optional[str] = None
    username: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    hashed_password: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_new: bool = False
    role: Optional[UserRole] = None


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
