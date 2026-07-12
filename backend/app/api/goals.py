"""Goals API routes."""
from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import math

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.schemas.schemas import GoalCreate, GoalOut

router = APIRouter()


def compute_required_sip(target: float, years: int, annual_return: float = 0.10) -> float:
    """Compute required monthly SIP to reach target in N years at given annual return."""
    if years <= 0:
        return target
    r = annual_return / 12  # monthly rate
    n = years * 12
    if r == 0:
        return target / n
    # FV of annuity: FV = SIP * [(1+r)^n - 1] / r
    # SIP = FV * r / [(1+r)^n - 1]
    sip = target * r / ((1 + r) ** n - 1)
    return round(sip, 2)


@router.post("/create", response_model=GoalOut, status_code=201)
async def create_goal(
    body: GoalCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    import datetime
    current_year = datetime.datetime.now().year
    years_to_goal = body.target_year - current_year

    goal = Goal(
        **body.model_dump(),
        user_id=current_user.id,
        required_monthly_sip=compute_required_sip(body.target_amount, years_to_goal),
    )
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return GoalOut.model_validate(goal)


@router.get("/{user_id}", response_model=List[GoalOut])
async def list_goals(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.role not in ("rm", "admin") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.priority, Goal.created_at)
    )
    goals = result.scalars().all()
    return [GoalOut.model_validate(g) for g in goals]


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    if goal.user_id != current_user.id and current_user.role not in ("rm", "admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    await db.delete(goal)
