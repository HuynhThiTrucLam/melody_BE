from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from core import config, security
from services.user_service import get_or_create_user
from core.config import logger

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class GoogleAuthRequest(BaseModel):
    id_token: str


@router.post("/auth/google")
async def google_login(payload: GoogleAuthRequest):
    try:
        idinfo = id_token.verify_oauth2_token(
            payload.id_token, google_requests.Request(), config.GOOGLE_CLIENT_ID
        )
    except (ValueError, Exception) as e:
        logger.error(f"google_login:: ValueError: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_or_create_user(idinfo)
    jwt_token = security.create_access_token({"sub": str(user["_id"])})
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "is_new": user.get("is_new"),
    }
