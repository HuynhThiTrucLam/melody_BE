from datetime import datetime, timedelta
import requests
import json
from core.config import (
    RAPID_API_DOWNLOAD_HOST,
    logger,
    RAPID_API_KEY,
    RAPID_API_HOST,
    RAPID_API_URL,
    CACHE_EXPIRE_TIME,
    RAPID_API_DOWNLOAD_URL,
)
from models.tracks import (
    TrackList,
    TrackSearch,
    TopTrendingTracks,
    Period,
    TrendingTracksResponse,
    DownloadTrackResponse,
    TrackLyricsResponse,
)
from db.mongo import search_history_collection


async def search_music_handler(data: TrackSearch):
    try:
        query = data.query
        offset = data.offset
        limit = data.limit
        url = f"{RAPID_API_URL}/search/"
        querystring = {
            "type": "tracks",
            "offset": offset,
            "limit": limit,
            "numberOfTopResults": "5",
            "q": query,
        }
        querystring_json = json.dumps(querystring)
        logger.info(f"Searching for music: {querystring_json}")
        search_history = await search_history_collection.find_one(
            {"query": querystring_json, "expires_at": {"$gt": datetime.now()}}
        )
        if search_history:
            logger.info(f"Found search history for {query}")
            result = TrackList(**search_history["result"])
            return result

        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": RAPID_API_HOST,
        }

        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        list_of_tracks = response.json().get("tracks", [])
        result = TrackList(
            items=list_of_tracks,
            totalCount=len(list_of_tracks),
        )
        await search_history_collection.update_one(
            {"query": querystring_json},
            {
                "$set": {
                    "result": result.model_dump(),
                    "expires_at": datetime.now() + timedelta(days=CACHE_EXPIRE_TIME),
                }
            },
            upsert=True,
        )
        return result
    except Exception as e:
        logger.error(f"Error searching music: {e}")
        raise e


async def top_trending_tracks_handler(data: TopTrendingTracks):
    try:
        country = data.country
        period = data.period
        url = f"{RAPID_API_URL}/top_200_tracks"
        querystring = {"country": country, "period": period}
        if period == Period.weekly:
            # Get latest Thursday
            today = datetime.now()
            thursday = today - timedelta(days=today.weekday())
            date = thursday.strftime("%Y-%m-%d")
            querystring["date"] = date

        querystring_json = json.dumps(querystring)
        logger.info(f"Getting top trending tracks: {querystring_json}")
        search_history = await search_history_collection.find_one(
            {"query": querystring_json, "expires_at": {"$gt": datetime.now()}}
        )
        if search_history:
            logger.info(f"Found search history for {country} and {period}")
            result = TrendingTracksResponse(**search_history["result"])
            return result

        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": RAPID_API_HOST,
        }

        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        list_of_tracks = response.json()
        result = TrendingTracksResponse(
            tracks=list_of_tracks,
        )
        await search_history_collection.update_one(
            {"query": querystring_json},
            {
                "$set": {
                    "result": result.model_dump(),
                    "expires_at": datetime.now() + timedelta(days=CACHE_EXPIRE_TIME),
                }
            },
            upsert=True,
        )
        return result
    except Exception as e:
        logger.error(f"Error getting top trending tracks: {e}")
        raise e


async def download_music_handler(id: str):
    try:
        # Check if this download is already cached
        query_key = f"download_{id}"
        cached_download = await search_history_collection.find_one(
            {"query": query_key, "expires_at": {"$gt": datetime.now()}}
        )

        if cached_download:
            logger.info(f"Found cached download for track ID: {id}")
            result = DownloadTrackResponse(**cached_download["result"])
            return result

        # Make API request if not cached
        querystring = {"songId": f"https://open.spotify.com/track/{id}"}
        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": RAPID_API_DOWNLOAD_HOST,
        }

        response = requests.get(
            RAPID_API_DOWNLOAD_URL, headers=headers, params=querystring
        )
        response.raise_for_status()
        response_data = response.json()

        # Parse into Pydantic model
        result = DownloadTrackResponse(**response_data)

        # Save to cache
        await search_history_collection.update_one(
            {"query": query_key},
            {
                "$set": {
                    "result": result.model_dump(),
                    "expires_at": datetime.now() + timedelta(days=CACHE_EXPIRE_TIME),
                }
            },
            upsert=True,
        )

        return result
    except Exception as e:
        logger.error(f"Error downloading music: {e}")
        raise e


async def get_track_lyrics_handler(id: str):
    try:
        # Check if lyrics are already cached
        query_key = f"lyrics_{id}"
        cached_lyrics = await search_history_collection.find_one(
            {"query": query_key, "expires_at": {"$gt": datetime.now()}}
        )

        if cached_lyrics:
            logger.info(f"Found cached lyrics for track ID: {id}")
            result = TrackLyricsResponse(**cached_lyrics["result"])
            return result

        # Make API request if not cached
        url = f"{RAPID_API_URL}/track_lyrics/"
        querystring = {"id": id}

        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": RAPID_API_HOST,
        }

        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        response_data = response.json()

        # Parse into Pydantic model
        result = TrackLyricsResponse(**response_data)

        # Save to cache
        await search_history_collection.update_one(
            {"query": query_key},
            {
                "$set": {
                    "result": result.model_dump(),
                    "expires_at": datetime.now() + timedelta(days=CACHE_EXPIRE_TIME),
                }
            },
            upsert=True,
        )

        return result
    except Exception as e:
        logger.error(f"Error getting track lyrics: {e}")
        raise e
