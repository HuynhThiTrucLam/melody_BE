import httpx
from fastapi import APIRouter

router = APIRouter()

AUDIOUS_BASE_URL = "https://api.audius.co"


async def get_audius_data(endpoint: str):
    """Helper function to fetch data from Audius API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"${AUDIOUS_BASE_URL}{endpoint}")
        response.raise_for_status()  # Raise exception for non-2xx responses
        return response.json()


@router.get("/tracks/{track_id}")
async def get_track(track_id: str):
    """Route to fetch track details from Audius."""
    endpoint = f"/v1/tracks/{track_id}"
    track_data = await get_audius_data(endpoint)
    return track_data
