from db.mongo import users_collection
from models.user import User, UserCreate
from core import security
from datetime import datetime
from typing import Optional, Dict, Any


async def get_or_create_user(idinfo: dict) -> Dict[str, Any]:
    user_data = User(
        email=idinfo.get("email"),
        name=idinfo.get("name"),
        picture=idinfo.get("picture"),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        username=idinfo.get("email"),  # Use email as username for Google auth
    )
    user = await users_collection.find_one({"email": user_data.email})
    if not user:
        result = await users_collection.insert_one(user_data.model_dump())
        user = await users_collection.find_one({"_id": result.inserted_id})
        user["_id"] = str(user["_id"])
        user["is_new"] = True
    return user


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    user = await users_collection.find_one({"username": username})
    if user:
        user["_id"] = str(user["_id"])
    return user


async def create_user(user_data: UserCreate) -> Dict[str, Any]:
    hashed_password = security.get_hash_code(user_data.password)

    user = User(
        username=user_data.username,
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    result = await users_collection.insert_one(user.model_dump())
    created_user = await users_collection.find_one({"_id": result.inserted_id})
    created_user["_id"] = str(created_user["_id"])
    created_user["is_new"] = True

    return created_user


async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = await get_user_by_username(username)
    if not user:
        return None
    if not security.verify_hashed_code(password, user.get("hashed_password")):
        return None
    return user
