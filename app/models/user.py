from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    hashed_password: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_new: bool = False


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str
