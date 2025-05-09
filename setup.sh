#!/bin/bash

# Color definitions for output
RESET="\033[0m"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
RED="\033[31m"

# Set up virtual environment
echo -e "${GREEN}Setting up virtual environment...${RESET}"
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create virtual environment.${RESET}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${RESET}"
source venv/bin/activate

# Install required packages
echo -e "${YELLOW}Installing required dependencies...${RESET}"
pip install --upgrade pip
pip install fastapi uvicorn httpx
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${RESET}"
    exit 1
fi

# Display a message about project structure
echo -e "${GREEN}Setting up the project structure...${RESET}"
mkdir -p app/api app/services app/models

# Create main.py file
echo -e "${YELLOW}Creating main.py...${RESET}"
cat <<EOF > app/main.py
from fastapi import FastAPI
from app.api import audius

app = FastAPI()

# Include Audius-related routes
app.include_router(audius.router)
EOF

# Create audius.py file
echo -e "${YELLOW}Creating api/audius.py...${RESET}"
cat <<EOF > app/api/audius.py
import httpx
from fastapi import APIRouter

router = APIRouter()

AUDIOUS_BASE_URL = "https://api.audius.co"

async def get_audius_data(endpoint: str):
    """Helper function to fetch data from Audius API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"\${AUDIOUS_BASE_URL}{endpoint}")
        response.raise_for_status()  # Raise exception for non-2xx responses
        return response.json()

@router.get("/tracks/{track_id}")
async def get_track(track_id: str):
    """Route to fetch track details from Audius."""
    endpoint = f"/v1/tracks/{track_id}"
    track_data = await get_audius_data(endpoint)
    return track_data
EOF

# Create audius_service.py file
echo -e "${YELLOW}Creating services/audius_service.py...${RESET}"
cat <<EOF > app/services/audius_service.py
from app.api.audius import get_audius_data

async def get_track_details(track_id: str):
    """Business logic to fetch track details and return useful data."""
    track_data = await get_audius_data(f"/v1/tracks/{track_id}")
    return track_data
EOF

# Create requirements.txt
echo -e "${YELLOW}Creating requirements.txt...${RESET}"
cat <<EOF > requirements.txt
fastapi
uvicorn
httpx
EOF

# Run FastAPI application
echo -e "${GREEN}Running FastAPI application...${RESET}"
uvicorn app.main:app --reload

# End of script
echo -e "${GREEN}Setup complete! You can access the app at http://127.0.0.1:8000${RESET}"
