"""Dashboard API — aggregates all data for main dashboard and RM view."""
from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_user, require_rm
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.simulation_result import SimulationResult, Recommendation
from app.schemas.schemas import DashboardResponse, UserOut, ProfileOut, GoalOut, CustomerSummary
from app.services.profile_service import compute_health_score

router = APIRouter()


@router.get("/{user_id}", response_model=DashboardResponse)
async def get_dashboard(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.role not in ("rm", "admin") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Profile
    p = await db.execute(select(FinancialProfile).where(FinancialProfile.user_id == user_id))
    profile = p.scalar_one_or_none()

    # Goals
    g = await db.execute(
        select(Goal).where(Goal.user_id == user_id, Goal.status == "active")
    )
    goals = g.scalars().all()

    # Latest simulation
    s = await db.execute(
        select(SimulationResult)
        .where(SimulationResult.user_id == user_id)
        .order_by(SimulationResult.computed_at.desc())
        .limit(1)
    )
    latest_sim = s.scalar_one_or_none()

    # Rec count
    r = await db.execute(
        select(func.count(Recommendation.id)).where(Recommendation.user_id == user_id)
    )
    rec_count = r.scalar() or 0

    # Compute aggregates
    net_worth = 0.0
    monthly_surplus = 0.0
    health_score = 0.0
    if profile:
        net_worth = float(profile.total_savings) + float(profile.total_investments) - float(profile.total_loans)
        monthly_surplus = (
            float(profile.monthly_income) * 0.70  # after tax approx
            - float(profile.monthly_expenses)
            - float(profile.monthly_emi)
        )
        health_score = float(profile.health_score or compute_health_score(profile))

    avg_prob = 0.0
    if goals:
        probs = [float(g.current_success_probability) for g in goals if g.current_success_probability]
        avg_prob = sum(probs) / len(probs) if probs else 0.0

    # User
    u = await db.execute(select(User).where(User.id == user_id))
    target_user = u.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    return DashboardResponse(
        user=UserOut.model_validate(target_user),
        profile=ProfileOut.model_validate(profile) if profile else None,
        goals=[GoalOut.model_validate(g) for g in goals],
        net_worth=net_worth,
        monthly_surplus=monthly_surplus,
        health_score=health_score,
        goals_summary={
            "total": len(goals),
            "avg_success_probability": round(avg_prob, 4),
            "on_track": sum(1 for g in goals if g.current_success_probability and g.current_success_probability >= 0.7),
        },
        latest_simulation=latest_sim.result_data if latest_sim else None,
        recommendations_count=rec_count,
    )


@router.get("/rm/customers", response_model=List[CustomerSummary])
async def rm_customer_list(
    current_rm: Annotated[User, Depends(require_rm)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 50,
):
    """RM view: list all customers with financial health summary."""
    users_result = await db.execute(
        select(User)
        .where(User.role == "customer", User.is_active == True)
        .offset(skip)
        .limit(limit)
        .order_by(User.created_at.desc())
    )
    customers = users_result.scalars().all()

    summaries = []
    for customer in customers:
        p = await db.execute(select(FinancialProfile).where(FinancialProfile.user_id == customer.id))
        profile = p.scalar_one_or_none()

        g = await db.execute(select(Goal).where(Goal.user_id == customer.id, Goal.status == "active"))
        goals = g.scalars().all()

        net_worth = 0.0
        health_score = 0.0
        if profile:
            net_worth = float(profile.total_savings) + float(profile.total_investments) - float(profile.total_loans)
            health_score = float(profile.health_score or 0)

        probs = [float(g.current_success_probability) for g in goals if g.current_success_probability]
        avg_prob = sum(probs) / len(probs) if probs else 0.0

        # Auto-generate discussion points
        discussion_points = []
        if profile:
            if float(profile.monthly_expenses) / float(profile.monthly_income) > 0.7:
                discussion_points.append("High expense ratio — discuss expense optimization")
            if float(profile.total_loans) > float(profile.monthly_income) * 24:
                discussion_points.append("High debt burden — consider loan restructuring")
            if avg_prob < 0.6:
                discussion_points.append("Goals at risk — review investment strategy")
            if float(profile.equity_allocation) < 0.3 and profile.age < 45:
                discussion_points.append("Under-allocated to equity for age profile")
        if not discussion_points:
            discussion_points = ["Portfolio on track — reinforce positive behavior"]

        risk_level = "high" if avg_prob < 0.5 else ("medium" if avg_prob < 0.75 else "low")

        summaries.append(CustomerSummary(
            user=UserOut.model_validate(customer),
            profile=ProfileOut.model_validate(profile) if profile else None,
            health_score=health_score,
            net_worth=net_worth,
            goals_count=len(goals),
            avg_success_probability=avg_prob,
            risk_level=risk_level,
            discussion_points=discussion_points,
            last_active=customer.updated_at,
        ))

    return summaries
