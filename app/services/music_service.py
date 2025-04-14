from datetime import datetime, timedelta
import requests
import json
from core.config import logger, RAPID_API_KEY, RAPID_API_HOST, RAPID_API_URL
from models.tracks import (
    TrackList,
    TrackSearch,
    TopTrendingTracks,
    Period,
    TrendingTracksResponse,
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
            {"query": querystring_json}
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
        await search_history_collection.insert_one(
            {"query": querystring_json, "result": result.model_dump()}
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
        await search_history_collection.insert_one(
            {
                "query": querystring_json,
                "result": result.model_dump(),
                "expires_at": datetime.now() + timedelta(days=1),
            }
        )
        return result
    except Exception as e:
        logger.error(f"Error getting top trending tracks: {e}")
        raise e
