import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

def _get_auth_settings() -> tuple[str, str, str]:
    username = os.environ["AUTH_USERNAME"]
    password = os.environ["AUTH_PASSWORD"]
    secret_key = os.environ["JWT_SECRET_KEY"]
    if len(secret_key.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes")

    return username, password, secret_key


def validate_auth_config() -> None:
    _get_auth_settings()


def create_access_token(username: str, secret_key: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + ACCESS_TOKEN_LIFETIME
    return jwt.encode(
        {
            "sub": username,
            "iat": now,
            "exp": expires_at,
        },
        secret_key,
        algorithm=JWT_ALGORITHM,
    )

def get_current_user(
    credentials: Annotated[
        str | None,
        Depends(oauth2_scheme),
    ],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, _, secret_key = _get_auth_settings()
    try:
        claims = jwt.decode(
            credentials,
            secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    username = claims.get("sub")
    if not isinstance(username, str) or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username
