from app.api.audius import get_audius_data

async def get_track_details(track_id: str):
    """Business logic to fetch track details and return useful data."""
    track_data = await get_audius_data(f"/v1/tracks/{track_id}")
    return track_data
