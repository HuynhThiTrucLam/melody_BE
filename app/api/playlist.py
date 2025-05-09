

from fastapi import APIRouter
from app.services import playlist as playlist_service
from app.models.playlist import PlaylistCreate, Playlist, PlaylistUpdate


router = APIRouter()

@router.post("/create", response_model=Playlist)
async def create_playlist(playlist: PlaylistCreate):
    return await playlist_service.create_playlist(playlist)


@router.get("/{playlist_id}", response_model=Playlist)
async def get_playlist(playlist_id: str):
    return await playlist_service.get_playlist(playlist_id)


@router.get("/user/{user_id}", response_model=list[Playlist])
async def get_user_playlists(user_id: str):
    return await playlist_service.get_user_playlists(user_id)


@router.put("/{playlist_id}", response_model=Playlist)
async def update_playlist(playlist_id: str, playlist: PlaylistUpdate):
    return await playlist_service.update_playlist(playlist_id, playlist)


@router.delete("/{playlist_id}", response_model=None)
async def delete_playlist(playlist_id: str):
    return await playlist_service.delete_playlist(playlist_id)


@router.post("/{playlist_id}/tracks", response_model=Playlist)
async def add_track_to_playlist(playlist_id: str, track_id: str):
    return await playlist_service.add_track_to_playlist(playlist_id, track_id)
