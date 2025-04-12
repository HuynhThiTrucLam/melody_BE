from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import audius
from api import google_auth
from api import auth


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include Audius-related routes
app.include_router(audius.router, prefix="/api/v1")
app.include_router(google_auth.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")