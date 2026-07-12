"""Financial Profile routes."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.schemas.schemas import ProfileCreate, ProfileUpdate, ProfileOut
from app.services.profile_service import compute_health_score

router = APIRouter()


@router.post("/create", response_model=ProfileOut, status_code=201)
async def create_profile(
    body: ProfileCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Check if profile already exists
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")

    profile = FinancialProfile(**body.model_dump(), user_id=current_user.id)
    profile.health_score = compute_health_score(profile)

    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return ProfileOut.model_validate(profile)


@router.get("/{user_id}", response_model=ProfileOut)
async def get_profile(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Allow RM to view any profile, customers can only view their own
    if current_user.role not in ("rm", "admin") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return ProfileOut.model_validate(profile)


@router.put("/update", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create first.")

    for key, value in body.model_dump().items():
        setattr(profile, key, value)
    profile.health_score = compute_health_score(profile)

    await db.flush()
    await db.refresh(profile)
    return ProfileOut.model_validate(profile)
