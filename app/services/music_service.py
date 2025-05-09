from datetime import datetime, timedelta
import http
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
    PopularSongsResponse,
    TrackList,
    TrackSearch,
    TopTrendingTracks,
    Period,
    TrendingTracksResponse,
    DownloadTrackResponse,
    TrackLyricsResponse,
    Country,
)
from db.mongo import search_history_collection, tracks_collection
import asyncio
import os


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
        {
            "_id": 1,
            "name": 1,
            "artists": 1,
            "albumOfTrack": 1,
            "genre": 1,
            "embedding": 1,
        },
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


async def get_popular_songs_from_api(country: Country):
    try:
        # Convert country to lowercase and handle special case
        country_key = country.lower()

        # Map of available mock files
        mock_files = {
            "vn": "popular_vn_songs.json",
            "global": "popular_global_songs.json",
            "kr": "porpular_kr_songs.json",  # Note typo in filename
            "us": "porpular_usuk_songs.json",  # Note typo in filename
            "gb": "porpular_usuk_songs.json",  # Use same file for GB
        }

        # Default to global if country not found
        if country_key not in mock_files:
            logger.warning(f"No mock data for country {country}, using global")
            country_key = "global"

        # Use absolute path instead of relative path
        import os

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        file_path = os.path.join(base_dir, "mocks", mock_files[country_key])

        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Mock file {file_path} not found, using global")
            file_path = os.path.join(base_dir, "mocks", "popular_global_songs.json")

            # If global file also doesn't exist, use fallback data
            if not os.path.exists(file_path):
                logger.warning(f"Global mock file also not found, using hardcoded data")
                raise FileNotFoundError("All mock files are missing")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Successfully loaded mock data from {file_path}")
            return PopularSongsResponse(data=data)
    except Exception as e:
        logger.error(f"Error getting popular songs: {e}")
        # Fallback to hardcoded data if all else fails
        fallback_data = [
            {
                "title": "Die With A Smile",
                "artist": "Lady Gaga, Bruno Mars",
                "genre": "Pop",
                "year": "2025",
            },
            {
                "title": "Abracadabra",
                "artist": "Lady Gaga",
                "genre": "Pop",
                "year": "2025",
            },
            {
                "title": "BIRDS OF A FEATHER",
                "artist": "Billie Eilish",
                "genre": "Pop",
                "year": "2025",
            },
            {
                "title": "Timeless",
                "artist": "The Weeknd",
                "genre": "R&B",
                "year": "2025",
            },
            {
                "title": "like JENNIE",
                "artist": "JENNIE",
                "genre": "K-pop",
                "year": "2025",
            },
        ]
        return PopularSongsResponse(data=fallback_data)


async def get_popular_songs_handler(country: Country):
    """Get popular songs from Audius API with improved performance"""
    try:
        # Check cache for final results with a more specific key (including timestamp)
        cache_key = f"popular_songs_{country}"
        cached_results = await search_history_collection.find_one(
            {"query": cache_key, "expires_at": {"$gt": datetime.now()}}
        )

        if cached_results:
            logger.info(f"Found cached popular songs for {country}")
            return cached_results["result"]["items"]

        # If not cached, proceed with API calls
        popular_songs = await get_popular_songs_from_api(country)

        import random

        # Limit to 10 songs to reduce processing time
        sample_size = min(10, len(popular_songs.data))
        popular_songs = random.sample(popular_songs.data, sample_size)

        # Use a semaphore to limit concurrent API calls (to avoid rate limiting)
        semaphore = asyncio.Semaphore(5)  # Maximum 5 concurrent requests

        async def search_with_timeout(song):
            """Execute search with timeout and semaphore to prevent hanging"""
            try:
                async with semaphore:
                    song_name = song.title
                    artist_name = song.artist
                    # Use a timeout to prevent slow API calls
                    return await asyncio.wait_for(
                        search_music_handler(
                            TrackSearch(query=f"{song_name} {artist_name}", limit=1)
                        ),
                        timeout=5.0,  # 5 second timeout
                    )
            except asyncio.TimeoutError:
                logger.warning(f"Timeout searching for {song.title} by {song.artist}")
                return None
            except Exception as e:
                logger.warning(f"Error searching for {song.title}: {str(e)}")
                return None

        # Create and execute search tasks with better error handling
        search_tasks = [search_with_timeout(song) for song in popular_songs]
        search_results = await asyncio.gather(*search_tasks)

        # Process results
        result = []
        serializable_result = []

        for i, track_data in enumerate(search_results):
            if (
                not track_data
                or not hasattr(track_data, "items")
                or not track_data.items
            ):
                # Skip invalid results
                result.append(None)
                serializable_result.append(None)
                continue

            track_item = track_data.items[0]
            result.append(track_item)
            serializable_result.append(track_item.model_dump())

        # Cache the final results with a reasonable expiration time
        await search_history_collection.update_one(
            {"query": cache_key},
            {
                "$set": {
                    "result": {"items": serializable_result},
                    "expires_at": datetime.now()
                    + timedelta(hours=24),  # Increase cache time
                }
            },
            upsert=True,
        )

        return result
    except Exception as e:
        logger.error(f"Error getting popular songs: {e}")
        raise e
