"""Authentication routes: register and login."""
import time
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter()

# ── Simple in-memory rate limiter ──────────────────────────────────────────
# Tracks request timestamps per IP. Resets on process restart.
_attempts: dict[str, list[float]] = {}

def _check_rate_limit(request: Request, max_attempts: int = 5, window_seconds: int = 60):
    """Allow max_attempts requests per window_seconds per IP."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - window_seconds

    if client_ip not in _attempts:
        _attempts[client_ip] = []

    # Purge old entries
    _attempts[client_ip] = [t for t in _attempts[client_ip] if t > window_start]

    if len(_attempts[client_ip]) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Try again in {window_seconds} seconds.",
        )

    _attempts[client_ip].append(now)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _check_rate_limit(request, max_attempts=3, window_seconds=300)  # 3 per 5 minutes
    # Check duplicate
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        full_name=user.full_name,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _check_rate_limit(request, max_attempts=10, window_seconds=60)  # 10 per minute
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        full_name=user.full_name,
        role=user.role,
    )
