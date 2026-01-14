"""
Authentication and Authorization
JWT tokens, API keys, password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from app_config import get_config
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = config.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.jwt_expire_minutes

# Security schemes
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[int] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return {"user_id": user_id, "username": payload.get("username")}


async def get_current_user_from_api_key(
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[dict]:
    """Get current user from API key"""
    if api_key is None:
        return None
    
    # In a real implementation, look up API key in database
    # For now, return a placeholder
    # TODO: Implement database lookup
    return {"user_id": 1, "api_key": api_key}


async def get_current_user(
    token_user: Optional[dict] = Depends(get_current_user_from_token),
    api_key_user: Optional[dict] = Depends(get_current_user_from_api_key)
) -> dict:
    """Get current user from either token or API key"""
    if token_user:
        return token_user
    elif api_key_user:
        return api_key_user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    token_user: Optional[dict] = Depends(get_current_user_from_token),
    api_key_user: Optional[dict] = Depends(get_current_user_from_api_key)
) -> Optional[dict]:
    """Get current user if authenticated, None otherwise"""
    if token_user:
        return token_user
    elif api_key_user:
        return api_key_user
    else:
        return None


def generate_api_key() -> str:
    """Generate a new API key"""
    import secrets
    return f"sk_{secrets.token_urlsafe(32)}"
