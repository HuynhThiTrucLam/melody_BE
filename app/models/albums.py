from pydantic import BaseModel
from typing import List, Optional


class ImageSource(BaseModel):
    url: str
    width: int
    height: int


class CoverArt(BaseModel):
    sources: List[ImageSource]


class SharingInfo(BaseModel):
    shareUrl: str


class Album(BaseModel):
    uri: str
    id: str
    name: str
    coverArt: CoverArt
    sharingInfo: Optional[SharingInfo] = None


class ArtistProfile(BaseModel):
    name: str


class Artist(BaseModel):
    uri: str
    profile: ArtistProfile


class Artists(BaseModel):
    items: List[Artist]
