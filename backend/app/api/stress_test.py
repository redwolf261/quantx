"""Stress Test API routes."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.models.financial_profile import FinancialProfile
from app.schemas.schemas import StressTestRequest, StressTestResult
from app.engines.stress_test import StressTestEngine

router = APIRouter()


@router.post("/run", response_model=StressTestResult)
async def run_stress_test(
    body: StressTestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    prof_result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = prof_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Create a financial profile first")

    goal = None
    if body.goal_id:
        g = await db.execute(select(Goal).where(Goal.id == body.goal_id))
        goal = g.scalar_one_or_none()

    target_amount = float(goal.target_amount) if goal else None
    initial_wealth = float(profile.total_savings) + float(profile.total_investments)

    engine = StressTestEngine(profile)
    result = engine.run(
        monthly_sip=body.monthly_sip,
        horizon_years=body.horizon_years,
        target_amount=target_amount,
        scenarios=body.scenarios,
    )

    return StressTestResult(
        goal_id=body.goal_id,
        horizon_years=body.horizon_years,
        base_result=result["base"],
        scenarios=result["scenarios"],
    )
