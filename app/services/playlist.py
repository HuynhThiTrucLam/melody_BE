from app.models.playlist import (
    Playlist,
    PlaylistCreate,
    PlaylistUpdate,
    PlaylistDelete,
    PlaylistResponse,
)
from app.db.mongo import playlists_collection, tracks_collection, users_collection
from app.models.tracks import Track, TrackItem
from app.models.user import UserResponse
from app.core.config import logger
from datetime import datetime
from fastapi import HTTPException
from bson.objectid import ObjectId


async def create_playlist(playlist: PlaylistCreate) -> Playlist:
    try:
        data = playlist.dict()
        if playlist.tracks:
            track_ids = playlist.tracks
            cursor = tracks_collection.find({"_id": {"$in": track_ids}})
            tracks = await cursor.to_list(length=None)
            tracks = [TrackItem(data=Track(**track)) for track in tracks]

            first_track = tracks[0]
            image = first_track.get_image()
            data["tracks"] = tracks
            data["image"] = image

        user_id = playlist.user_id
        user = await users_collection.find_one({"_id": ObjectId(user_id)})

        if not user:
            raise HTTPException(
                status_code=404, detail=f"User with id {user_id} not found"
            )

        data["user"] = UserResponse(**user)
        data["user"].id = str(user_id)
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()

        data = Playlist(**data)
        res = await playlists_collection.insert_one(data.dict())
        data.id = str(res.inserted_id)
        return data

    except Exception as e:
        logger.error(f"Error creating playlist: {e}")
        raise e


async def get_playlist(playlist_id: str) -> Playlist:
    try:
        playlist = await playlists_collection.find_one({"_id": ObjectId(playlist_id)})
        if not playlist:
            raise HTTPException(
                status_code=404, detail=f"Playlist with id {playlist_id} not found"
            )
        playlist["id"] = str(playlist["_id"])
        del playlist["_id"]
        playlist = Playlist(**playlist)
        return playlist
    except Exception as e:
        logger.error(f"Error getting playlist: {e}")
        raise e


async def get_user_playlists(user_id: str) -> list[Playlist]:
    try:
        cursor = playlists_collection.find({"user.id": user_id})
        playlists = await cursor.to_list(length=None)

        if not playlists:
            raise HTTPException(
                status_code=404, detail=f"No playlists found for user with id {user_id}"
            )
        res = []
        for playlist in playlists:
            playlist["id"] = str(playlist["_id"])
            res.append(Playlist(**playlist))

        return res
    except Exception as e:
        logger.error(f"Error getting user playlists: {e}")
        raise e


async def update_playlist(playlist_id: str, playlist: PlaylistUpdate) -> Playlist:
    try:
        existing_playlist = await get_playlist(playlist_id)
        if not existing_playlist:
            raise HTTPException(
                status_code=404, detail=f"Playlist with id {playlist_id} not found"
            )

        playlist_data = existing_playlist.dict()
        for key, value in playlist.dict().items():
            if value is not None:
                playlist_data[key] = value

        playlist_data["updated_at"] = datetime.now()

        await playlists_collection.update_one(
            {"_id": ObjectId(playlist_id)}, {"$set": playlist_data}
        )
        playlist_data["id"] = str(playlist_id)
        return Playlist(**playlist_data)
    except Exception as e:
        logger.error(f"Error updating playlist: {e}")
        raise e


async def delete_playlist(playlist_id: str) -> None:
    try:
        existing_playlist = await get_playlist(playlist_id)
        if not existing_playlist:
            raise HTTPException(
                status_code=404, detail=f"Playlist with id {playlist_id} not found"
            )
        await playlists_collection.delete_one({"_id": ObjectId(playlist_id)})
    except Exception as e:
        logger.error(f"Error deleting playlist: {e}")
        raise e


async def add_track_to_playlist(playlist_id: str, track_id: str) -> Playlist:
    try:
        existing_playlist = await get_playlist(playlist_id)
        if not existing_playlist:
            raise HTTPException(
                status_code=404, detail=f"Playlist with id {playlist_id} not found"
            )

        track = await tracks_collection.find_one({"_id": track_id})
        if not track:
            raise HTTPException(
                status_code=404, detail=f"Track with id {track_id} not found"
            )

        if existing_playlist.tracks and track_id in [
            track.id for track in existing_playlist.tracks
        ]:
            raise HTTPException(
                status_code=400, detail=f"Track with id {track_id} already in playlist"
            )

        length = len(existing_playlist.tracks) if existing_playlist.tracks else 0
        track_item = TrackItem(data=Track(**track))
        if length == 0:
            existing_playlist.image = track_item.get_image()
            existing_playlist.tracks = [track_item]
        else:
            existing_playlist.tracks.append(track_item)

        existing_playlist.updated_at = datetime.now()
        await playlists_collection.update_one(
            {"_id": ObjectId(playlist_id)}, {"$set": existing_playlist.dict()}
        )
        return existing_playlist
    except Exception as e:
        logger.error(f"Error adding track to playlist: {e}")
        raise e
