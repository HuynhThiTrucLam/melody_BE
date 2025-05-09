from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import audius
from api import google_auth
from api import auth
from api import music
from api import health
from api import playlist

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include Audius-related routes
app.include_router(audius.router, prefix="/api/v1", tags=["audius"])
app.include_router(google_auth.router, prefix="/api/v1", tags=["google_auth"])
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(music.router, prefix="/api/v1", tags=["music"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(playlist.router, prefix="/api/v1", tags=["playlist"])
