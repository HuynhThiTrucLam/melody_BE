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

    def model_dump(self):
        """Convert model to dictionary, excluding None values."""
        data = {
            key: value
            for key, value in self.__dict__.items()
            if value is not None and not key.startswith("_")
        }
        # Convert _id to string if it exists
        if hasattr(self, "_id") and self._id is not None:
            data["_id"] = str(self._id)
        return data


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
