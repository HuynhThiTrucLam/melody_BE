from fastapi import APIRouter, HTTPException, Depends, Query
from models.tracks import Country, Period, TrackSearch, TopTrendingTracks
from services.music_service import (
    search_music_handler,
    top_trending_tracks_handler,
    download_music_handler,
    get_track_lyrics_handler,
)
from models.user import UserRole
from api.deps import validate_role


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
