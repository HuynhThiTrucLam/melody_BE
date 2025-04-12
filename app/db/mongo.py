from motor.motor_asyncio import AsyncIOMotorClient
from core import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.get_default_database(config.MONGO_DB)
users_collection = db.get_collection("users")
