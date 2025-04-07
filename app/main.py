from fastapi import FastAPI
from app.api import audius

app = FastAPI()

# Include Audius-related routes
app.include_router(audius.router)
