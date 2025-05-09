from datetime import datetime, timedelta
import numpy as np
import requests
import json
from app.utils import create_hybrid_embedding
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
    MusicTrack,
)
from db.mongo import search_history_collection, tracks_collection


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

        search_history_collection.update_one(
            {"query": querystring_json},
            {
                "$set": {
                    "result": result.model_dump(),
                    "expires_at": datetime.now() + timedelta(days=CACHE_EXPIRE_TIME),
                }
            },
            upsert=True,
        )
        # Store the tracks in the database
        logger.info(f"Storing {len(result.items)} tracks in the database")
        for track in result.items:
            track_data = track.data.dict(exclude_none=True)
            track_data["created_at"] = datetime.now()
            track_data["updated_at"] = datetime.now()
            track_data["_id"] = track_data["id"]
            embedding = create_hybrid_embedding(song_metadata=track.data)
            track_data["embedding"] = embedding
            tracks_collection.update_one(
                {"_id": track_data["_id"]},
                {"$set": track_data},
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


# Get music detail by id
async def get_music_detail_by_id(id: str) -> MusicTrack:
    try:
        # Define cache keys for each endpoint
        info_key = f"track_infor_{id}"
        lyrics_key = f"lyrics_{id}"
        download_key = f"download_{id}"
        
        # Initialize variables to store results
        track_info = None
        lyrics_data = None
        download_data = None
        
        # Check cache for each endpoint
        info_cache = await search_history_collection.find_one(
            {"query": info_key, "expires_at": {"$gt": datetime.now()}}
        )
        lyrics_cache = await search_history_collection.find_one(
            {"query": lyrics_key, "expires_at": {"$gt": datetime.now()}}
        )
        download_cache = await search_history_collection.find_one(
            {"query": download_key, "expires_at": {"$gt": datetime.now()}}
        )
        
        # Get track info
        if info_cache:
            logger.info(f"Using cached track info for track ID: {id}")
            track_info = info_cache["result"]
        else:
            logger.info(f"Fetching track info for track ID: {id}")
            track_info = await get_music_infor_by_id(id)
            if not track_info:
                raise Exception(f"Failed to retrieve track info for ID: {id}")
        
        # Debug log to see actual structure
        logger.debug(f"Track info structure: {json.dumps(track_info, default=str)[:500]}...")
       
        # Get lyrics data
        if lyrics_cache:
            logger.info(f"Using cached lyrics for track ID: {id}")
            lyrics_data = lyrics_cache["result"]
        else:
            try:
                logger.info(f"Fetching lyrics for track ID: {id}")
                lyrics_data = await get_track_lyrics_handler(id)
            except Exception as e:
                logger.warning(f"Failed to get lyrics for track {id}: {e}")
                # Create a default lyrics response if needed
                lyrics_data = TrackLyricsResponse(
                    lyrics={
                        "syncType": "UNSYNCED",
                        "lines": [],
                        "provider": "unknown",
                        "providerLyricsId": "",
                        "providerDisplayName": "",
                        "syncLyricsUri": "",
                        "isDenseTypeface": False,
                        "alternatives": [],
                        "language": "",
                        "isRtlLanguage": False,
                        "capStatus": "",
                        "previewLines": []
                    },
                    colors={
                        "background": 0,
                        "text": 0,
                        "highlightText": 0
                    },
                    hasVocalRemoval=False
                )
   
        # Get download data
        if download_cache:
            logger.info(f"Using cached download data for track ID: {id}")
            download_data = download_cache["result"]
        else:
            try:
                logger.info(f"Fetching download data for track ID: {id}")
                download_data = await download_music_handler(id)
                if not download_data:
                    raise Exception(f"Failed to retrieve download data for ID: {id}")
            except Exception as e:
                logger.warning(f"Failed to get download URL for track {id}: {e}")
                raise Exception(f"Unable to get download information for track: {e}")
        
        # Construct the MusicTrack object
        try:
            # Extract track ID - handle different possible structures
            track_id = id  # Default to the input ID
            if isinstance(track_info, dict):
                if "track" in track_info and isinstance(track_info["track"], dict) and "id" in track_info["track"]:
                    track_id = track_info["track"]["id"]
                elif "id" in track_info:
                    track_id = track_info["id"]
            
            # Extract duration - handle different possible structures
            duration = 0  # Default duration
            if isinstance(track_info, dict):
                # Debug log to understand the structure
                logger.debug(f"Extracting duration from track_info keys: {list(track_info.keys())}")
                
                # Handle Spotify API response format with tracks array
                if "tracks" in track_info and isinstance(track_info["tracks"], list) and len(track_info["tracks"]) > 0:
                    track = track_info["tracks"][0]  # Get first track in array
                    logger.debug(f"Found track in tracks array with keys: {list(track.keys())}")
                    if "duration_ms" in track:
                        duration = track["duration_ms"]
                        logger.debug(f"Found duration_ms in tracks array: {duration}")
                # First check if duration is in the main track object
                elif "track" in track_info and isinstance(track_info["track"], dict):
                    track_obj = track_info["track"]
                    logger.debug(f"Track object keys: {list(track_obj.keys())}")
                    
                    if "duration_ms" in track_obj:
                        duration = track_obj["duration_ms"]
                    elif "duration" in track_obj:
                        duration = track_obj["duration"]
                    # Check for nested duration object
                    elif "duration" in track_obj and isinstance(track_obj["duration"], dict) and "totalMilliseconds" in track_obj["duration"]:
                        duration = track_obj["duration"]["totalMilliseconds"]
                
                # Check for duration in root object
                elif "duration_ms" in track_info:
                    duration = track_info["duration_ms"]
                elif "duration" in track_info:
                    # Check if duration is a dictionary or a direct value
                    if isinstance(track_info["duration"], dict) and "totalMilliseconds" in track_info["duration"]:
                        duration = track_info["duration"]["totalMilliseconds"]
                    else:
                        duration = track_info["duration"]
            
            logger.info(f"Extracted duration: {duration}")
            
            # Handle both dictionary and DownloadTrackResponse object
            if isinstance(download_data, dict):
                title = download_data["data"]["title"]
                artist = download_data["data"]["artist"]
                cover = download_data["data"]["cover"]
                download_link = download_data["data"]["downloadLink"]
                release_date = download_data["data"]["releaseDate"]
            else:
                title = download_data.data.title
                artist = download_data.data.artist
                cover = download_data.data.cover
                download_link = download_data.data.downloadLink
                release_date = download_data.data.releaseDate
            
            result = MusicTrack(
                id=track_id,
                name=title,
                artist=[artist],  # Wrap in list since artist is List[str]
                albumArt=cover,
                audioUrl=download_link,
                lyrics=lyrics_data,
                duration=duration,
                listener=0,
                releaseDate=release_date,
                nation=None
            )
            return result
        except KeyError as e:
            logger.error(f"Missing required field in data: {e}")
            raise Exception(f"Data missing required field: {e}")
        
    except Exception as e:
        logger.error(f"Error getting comprehensive music details: {e}")
        raise e


async def get_music_infor_by_id(id: str):
    try:
        # Check if details are already cached
        query_key = f"track_infor_{id}"
        cached_detail = await search_history_collection.find_one(
            {"query": query_key, "expires_at": {"$gt": datetime.now()}}
        )

        if cached_detail:
            logger.info(f"Found cached details for track ID: {id}")
            return cached_detail["result"]

        # Make API request if not cached
        url = f"{RAPID_API_URL}/tracks"
        querystring = {"ids": id}
        
        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": RAPID_API_HOST,
        }
        
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        result = response.json()
        
        # Save to cache
        await search_history_collection.update_one(
            {"query": query_key},
            {
                "$set": {
                    "result": result,
                    "expires_at": datetime.now() + timedelta(days=CACHE_EXPIRE_TIME),
                }
            },
            upsert=True,
        )
        
        return result
    except Exception as e:
        logger.error(f"Error getting music detail by id: {e}")
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
                    "expires_at": datetime.now() + timedelta(minutes=14),
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


async def find_similar_songs_atlas(song_id, n=5, filter_criteria=None):
    """Find similar songs using MongoDB Atlas vector search"""
    # Get source song embedding
    source_song = await tracks_collection.find_one({"_id": song_id})
    if not source_song or "embedding" not in source_song:
        return []

    query = {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": source_song["embedding"],
            "numCandidates": n * 10,  # Retrieve more candidates for better results
            "limit": n + 1,  # +1 to account for the source song
        }
    }

    # Add filters if needed
    if filter_criteria:
        query["$match"] = filter_criteria

    # Add filter to exclude the source song
    if "$match" not in query:
        query["$match"] = {"_id": {"$ne": song_id}}
    else:
        query["$match"]["_id"] = {"$ne": song_id}

    # Pipeline for aggregation
    pipeline = [
        query,
        {
            "$project": {
                "_id": 1,
                "title": 1,
                "artist": 1,
                "album": 1,
                "genre": 1,
                "similarity_score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    cursor = tracks_collection.aggregate(pipeline)
    results = await cursor.to_list(length=n)

    return results


async def find_similar_songs(song_id, n=5, filter_criteria=None):
    """Find similar songs based on embedding similarity"""
    source_song = await tracks_collection.find_one({"_id": song_id})
    if not source_song or "embedding" not in source_song:
        return []

    source_embedding = np.array(source_song["embedding"])

    # Prepare filter criteria
    query = {}
    if filter_criteria:
        query.update(filter_criteria)

    # Exclude the source song itself
    query["_id"] = {"$ne": song_id}

    # Fetch all potential matching songs (this can be optimized with larger datasets)
    cursor = tracks_collection.find(
        query,
        {"_id": 1, "name": 1, "artists": 1, "albumOfTrack": 1, "genre": 1, "embedding": 1},
    )
    potential_matches = await cursor.to_list(length=100)  # Limit to 100 for performance

    # Calculate similarity scores
    similar_songs = []
    for song in potential_matches:
        if "embedding" in song:
            target_embedding = np.array(song["embedding"])
            # Compute cosine similarity
            similarity = np.dot(source_embedding, target_embedding) / (
                np.linalg.norm(source_embedding) * np.linalg.norm(target_embedding)
            )
            if "embedding" in song:
                del song["embedding"]
            song["similarity_score"] = float(similarity)
            similar_songs.append(song)

    # Sort by similarity score and return top N
    similar_songs.sort(key=lambda x: x["similarity_score"], reverse=True)
    return similar_songs[:n]
