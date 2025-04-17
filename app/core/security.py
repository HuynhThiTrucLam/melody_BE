from datetime import datetime, timedelta
from core.config import logger
from jose import jwt, JWTError
from core import config
from passlib.context import CryptContext
from typing import Optional, List

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    except (JWTError, Exception) as e:
        return None


def verify_hashed_code(plain_code, hashed_code):
    return pwd_context.verify(plain_code, hashed_code)


def get_hash_code(code: str):
    return pwd_context.hash(code)
