from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core import security
from models.user import User, UserRole
from typing import List, Optional
from core.config import logger
from services.user_service import get_user_by_username

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[User]:
    """
    Validates the credentials and returns the current user.
    """
    if not credentials:
        return None

    payload = security.decode_access_token(credentials.credentials)
    if payload is None:
        return None

    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def validate_role(allowed_roles: List[UserRole]):
    """
    Dependency factory that validates if the current user has one of the allowed roles.
    Usage: @router.get("/endpoint", dependencies=[Depends(validate_role([UserRole.admin]))])
    """
    logger.info(f"Allowed roles: {allowed_roles}")

    async def role_validator(user: Optional[User] = Depends(get_current_user)):
        logger.info(f"User role: {user}")
        if not user or user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
            )
        return user

    return role_validator
