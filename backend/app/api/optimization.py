"""Optimization API routes."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.models.financial_profile import FinancialProfile
from app.models.simulation_result import Recommendation
from app.schemas.schemas import OptimizationRequest, OptimizationResult
from app.engines.optimizer import OptimizationEngine

router = APIRouter()


@router.post("/run", response_model=OptimizationResult)
async def run_optimization(
    body: OptimizationRequest,
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

    engine = OptimizationEngine(profile)
    result = engine.optimize(
        horizon_years=body.horizon_years,
        target_amount=target_amount,
        target_probability=body.target_probability,
        min_sip=body.min_sip,
        max_sip=body.max_sip,
        min_retirement_age=body.min_retirement_age,
        max_retirement_age=body.max_retirement_age,
    )

    # Persist recommendation
    rec = Recommendation(
        user_id=current_user.id,
        goal_id=body.goal_id,
        recommendation_type="sip_optimization",
        current_probability=result["current_probability"],
        optimized_probability=result["optimized_probability"],
        recommended_sip=result["recommended_sip"],
        optimization_data=result,
    )
    db.add(rec)
    await db.flush()

    return OptimizationResult(**result)
