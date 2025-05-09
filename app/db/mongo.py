from motor.motor_asyncio import AsyncIOMotorClient
from core import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.get_default_database(config.MONGO_DB)
users_collection = db.get_collection("users")
verification_codes_collection = db.get_collection("verification_codes")
tracks_collection = db.get_collection("tracks")
search_history_collection = db.get_collection("search_history")
playlists_collection = db.get_collection("playlists")
