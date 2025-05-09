from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.models.tracks import TrackItem
from app.models.user import UserResponse


class Playlist(BaseModel):
    id: Optional[str] = None
    name: str
    image: Optional[str] = None
    tracks: Optional[list[TrackItem]] = None
    user: UserResponse
    created_at: Optional[datetime] = datetime.now()
    updated_at: Optional[datetime] = datetime.now()

    class Config:
        orm_mode = True


class PlaylistCreate(BaseModel):
    name: str
    user_id: str
    tracks: Optional[list[str]] = None


class PlaylistUpdate(BaseModel):
    name: Optional[str] = None
    image: Optional[str] = None
    tracks: Optional[list[str]] = None


class PlaylistDelete(BaseModel):
    id: str


class PlaylistResponse(BaseModel):
    id: str
    name: str
    image: str
    tracks: list[TrackItem]
    user: UserResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
