import mimetypes
import os
from typing import List, Optional
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Query,
    BackgroundTasks,
    Body,
    Request,
)
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel
from models.tracks import Country, MusicTrack, Period, TrackSearch, TopTrendingTracks

from services.music_service import (
    find_similar_songs,
    find_similar_songs_atlas,
    search_music_handler,
    top_trending_tracks_handler,
    download_music_handler,
    get_track_lyrics_handler,
    get_popular_songs_handler,
    get_popular_songs_from_api,
    get_music_infor_by_id,
    get_music_detail_by_id,
)
from models.user import UserRole
from api.deps import validate_role
from datetime import datetime
from db.mongo import search_history_collection
from core.config import logger
import time
import hashlib
from pathlib import Path


router = APIRouter(tags=["music"], prefix="/music")


@router.get(
    "/",
    dependencies=[Depends(validate_role([UserRole.user, UserRole.admin]))],
)
async def get_music():
    return {"message": "Hello, World!"}


# Search for music
@router.get(
    "/search",
    # dependencies=[
    #     Depends(validate_role([UserRole.admin, UserRole.user, UserRole.artist]))
    # ],
)
async def search_music(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Limit of results"),
    offset: int = Query(0, description="Offset of results"),
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    data = TrackSearch(query=query, limit=limit, offset=offset)
    return await search_music_handler(data)


# Get music infor by id
@router.get(
    "/get-infor/{id}",
)
async def get_music_infor(id: str):
    return await get_music_infor_by_id(id)


# Get music detail by id
@router.get(
    "/get-detail/{id}",
)
async def get_music_detail(id: str) -> MusicTrack:
    return await get_music_detail_by_id(id)


# Top 200 tracks
@router.get(
    "/top-trending",
    dependencies=[
        Depends(validate_role([UserRole.admin, UserRole.user, UserRole.artist]))
    ],
)
async def top_trending_tracks(
    country: Country = Query(..., description="Country"),
    period: Period = Query(..., description="Period"),
):
    if not country.strip():
        raise HTTPException(status_code=400, detail="Country is required")

    data = TopTrendingTracks(country=country, period=period)
    return await top_trending_tracks_handler(data)


# Download music by id
@router.get(
    "/download/{id}",
)
async def download_music(id: str):
    return await download_music_handler(id)


# Get track lyrics by id
@router.get(
    "/lyrics/{id}",
)
async def get_track_lyrics(id: str):
    return await get_track_lyrics_handler(id)


@router.get("/similar-songs/{song_id}")
async def get_similar_songs(
    song_id: str, n: Optional[int] = Query(5, ge=1, le=50), genre: Optional[str] = None
):
    """Find similar songs to the given song ID"""
    # Prepare filter criteria
    filter_criteria = {}
    if genre:
        filter_criteria["genre"] = genre

    # Use MongoDB Atlas vector search if available
    try:
        similar_songs = await find_similar_songs_atlas(song_id, n, filter_criteria)
    except Exception as e:
        # Fall back to custom implementation
        similar_songs = await find_similar_songs(song_id, n, filter_criteria)

    if not similar_songs:
        raise HTTPException(
            status_code=404,
            detail="No similar songs found or source song not available",
        )

    return similar_songs


@router.get("/popular-songs")
async def get_popular_songs(
    country: Country = Query(..., description="Country"),
):
    """Get popular songs with optional background processing"""
    return await get_popular_songs_handler(country)
