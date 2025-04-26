from bson import ObjectId
from typing import Type
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from models.verification import SendCodeRequest, VerifyCodeRequest
from core import security
from models.user import UserCreate, UserLogin, UserUpdate, UserRole
from services.user_service import (
    create_user,
    get_user_by_username,
    authenticate_user,
    update_user_by_id,
)
from services.verification_service import (
    send_verification_code as send_code,
    verify_verification_code as verify_code,
)
from core.config import logger
from api.deps import get_current_user, validate_role

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str
    is_new: bool = False


@router.post("/auth/register", response_model=Token)
async def register_user(user_data: UserCreate):
    # Check if username already exists
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Create new user
    user = await create_user(user_data)

    # Create access token
    access_token = security.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "is_new": True}


@router.post("/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    user = await authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_new": user.is_new,
    }


@router.post("/auth/logout", dependencies=[Depends(get_current_user)])
async def logout():
    # Token invalidation would typically happen here
    # For JWT, client-side token removal is common
    return {"message": "Logged out successfully"}


@router.post("/send_verification_code")
async def send_verification_code(req: SendCodeRequest):
    logger.info(f"Sending verification code to {req.email} for {req.purpose}")
    result = await send_code(req.email, req.purpose)
    return result


@router.post("/verify_verification_code")
async def verify_verification_code(req: VerifyCodeRequest):
    result = await verify_code(req.email, req.code)
    return result


@router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate):
    try:
        user = await update_user_by_id(ObjectId(user_id), user_data)
        return user
    except AttributeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
