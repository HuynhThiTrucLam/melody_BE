from fastapi import APIRouter, HTTPException
from models.tracks import TrackSearch, TopTrendingTracks
from services.music_service import search_music_handler, top_trending_tracks_handler


router = APIRouter(tags=["music"], prefix="/music")


@router.get("/")
async def get_music():
    return {"message": "Hello, World!"}


# Search for music
@router.post("/search")
async def search_music(data: TrackSearch):
    if not data.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    return await search_music_handler(data)


# Top 200 tracks
@router.post("/top-trending")
async def top_trending_tracks(data: TopTrendingTracks):
    if not data.country.strip():
        raise HTTPException(status_code=400, detail="Country is required")

    return await top_trending_tracks_handler(data)
