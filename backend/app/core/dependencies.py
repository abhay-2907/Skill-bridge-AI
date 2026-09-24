"""
CareerPilot AI — FastAPI Dependencies
========================================
What is this?
  Reusable dependency functions injected into API route handlers via FastAPI's
  Depends() system.

Why dependency injection?
  - Avoids repeating auth logic in every route
  - Makes routes testable (swap dependencies in tests)
  - Clean separation of concerns

How Depends() works:
  FastAPI calls the dependency function before calling your route handler.
  The return value is passed as a parameter to the route.
  If the dependency raises an HTTPException, the route is never called.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token
from app.database.session import get_db
from app.models.models import User

# OAuth2PasswordBearer reads the Bearer token from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: Extract and validate JWT, return the current authenticated User.
    Raises 401 if token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    token_type: str = payload.get("type")
    if token_type != "access":
        raise credentials_exception

    # Fetch user from DB
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias dependency that ensures the user is active."""
    return current_user
