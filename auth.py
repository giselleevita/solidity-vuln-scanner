"""Authentication and authorization helpers."""

from datetime import UTC, datetime, timedelta
import hmac
import os
from typing import Optional

import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from app_config import get_config
from database import find_active_user_by_api_key, find_active_user_by_id
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
DEFAULT_JWT_SECRET = "change-this-secret-key-in-production"
SECRET_KEY = config.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.jwt_expire_minutes

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if SECRET_KEY == DEFAULT_JWT_SECRET:
        raise RuntimeError("JWT token issuance is disabled until JWT_SECRET_KEY is configured")

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    if SECRET_KEY == DEFAULT_JWT_SECRET:
        logger.warning("Rejecting JWT authentication because the default secret is configured")
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[dict]:
    """Get current user from JWT token"""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None

    user_id_value = payload.get("sub") or payload.get("user_id")
    try:
        user_id = int(user_id_value)
    except (TypeError, ValueError):
        user_id = None

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    db_user = find_active_user_by_id(user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "is_admin": db_user.is_admin,
        "auth_type": "jwt",
    }


def _bootstrap_api_key_users() -> list[dict]:
    entries = os.getenv("BOOTSTRAP_API_KEYS", "").strip()
    users: list[dict] = []
    if not entries:
        return users

    for raw_entry in entries.split(","):
        label, separator, key = raw_entry.partition(":")
        if not separator or not label.strip() or not key.strip():
            continue
        users.append(
            {
                "user_id": None,
                "username": label.strip(),
                "api_key": key.strip(),
                "auth_type": "bootstrap_api_key",
            }
        )
    return users


def lookup_api_key_principal(api_key: str) -> Optional[dict]:
    for user in _bootstrap_api_key_users():
        if hmac.compare_digest(user["api_key"], api_key):
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "auth_type": user["auth_type"],
            }

    db_user = find_active_user_by_api_key(api_key)
    if db_user is None or db_user.api_key is None:
        return None

    if not hmac.compare_digest(db_user.api_key, api_key):
        return None

    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "is_admin": db_user.is_admin,
        "auth_type": "database_api_key",
    }


def _extract_api_key(request: Request, header_api_key: Optional[str]) -> Optional[str]:
    if header_api_key:
        return header_api_key.strip()

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        return token or None

    return None


async def get_current_user_from_api_key(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[dict]:
    """Get current user from API key"""
    resolved_key = _extract_api_key(request, api_key)
    if resolved_key is None:
        return None

    return lookup_api_key_principal(resolved_key)


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


async def require_api_key_user(
    api_key_user: Optional[dict] = Depends(get_current_user_from_api_key),
) -> dict:
    """Require a valid API key principal."""
    if api_key_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key_user


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
