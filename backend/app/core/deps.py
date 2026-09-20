"""Shared FastAPI dependencies."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_access_token
from app.database import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise credentials_error

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user or not user.is_active:
        raise credentials_error
    return user


def get_optional_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User | None:
    """The public awareness tools work without an account — this keeps them anonymous-friendly."""
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        return None
    return db.query(User).filter(User.email == payload["sub"]).first()


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(roles)}",
            )
        return user

    return checker


# ------------------------------------------------------------------ rate limiting
# In-memory and per-process: enough to stop a runaway script or an accidental loop during a
# workshop demo. A multi-process deployment would need Redis; that is out of scope here and
# is documented as a limitation.
_buckets: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    limit = settings.RATE_LIMIT_PER_MINUTE
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = _buckets[client]

    while bucket and now - bucket[0] > 60:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a minute and try again.",
        )
    bucket.append(now)
