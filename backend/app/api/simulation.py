"""Simulation API — triggers Monte Carlo engine."""
from typing import Annotated
from uuid import UUID
import uuid as uuid_lib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.goal import Goal
from app.models.financial_profile import FinancialProfile
from app.models.simulation_result import SimulationResult as SimulationResultModel
from app.schemas.schemas import SimulationRequest, SimulationResult
from app.engines.monte_carlo import MonteCarloEngine
from app.engines.digital_twin import DigitalTwinEngine

router = APIRouter()


@router.post("/run", response_model=SimulationResult)
async def run_simulation(
    body: SimulationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Load profile
    prof_result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = prof_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="Create a financial profile first")

    # Load goal (optional)
    goal = None
    if body.goal_id:
        g_result = await db.execute(select(Goal).where(Goal.id == body.goal_id))
        goal = g_result.scalar_one_or_none()
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")

    # Build inputs
    initial_wealth = body.initial_wealth if body.initial_wealth is not None else (
        float(profile.total_savings) + float(profile.total_investments)
    )
    target_amount = body.target_amount if body.target_amount is not None else (
        float(goal.target_amount) if goal else None
    )

    # Run Digital Twin to get current monthly surplus
    twin = DigitalTwinEngine(profile)
    surplus_data = twin.compute_monthly_surplus()

    # Run Monte Carlo
    engine = MonteCarloEngine(
        initial_wealth=initial_wealth,
        monthly_sip=body.monthly_sip,
        horizon_years=body.horizon_years,
        equity_allocation=float(profile.equity_allocation),
        debt_allocation=float(profile.debt_allocation),
        risk_profile=profile.risk_profile.value,
        salary_growth_rate=float(profile.salary_growth_rate),
        inflation_rate=float(profile.inflation_rate),
        num_simulations=body.num_simulations,
    )
    result = engine.run(target_amount=target_amount)

    # Persist result
    sim_record = SimulationResultModel(
        user_id=current_user.id,
        goal_id=body.goal_id,
        simulation_type="monte_carlo",
        num_simulations=body.num_simulations,
        horizon_years=body.horizon_years,
        success_probability=result["success_probability"],
        median_corpus=result["median_corpus"],
        p10_corpus=result["p10_corpus"],
        p90_corpus=result["p90_corpus"],
        failure_probability=result["failure_probability"],
        result_data=result,
        parameters={
            "initial_wealth": initial_wealth,
            "monthly_sip": body.monthly_sip,
            "horizon_years": body.horizon_years,
        },
    )
    db.add(sim_record)

    # Update goal probability
    if goal and result.get("success_probability") is not None:
        goal.current_success_probability = result["success_probability"]

    await db.flush()
    await db.refresh(sim_record)

    return SimulationResult(
        simulation_id=sim_record.id,
        goal_id=body.goal_id,
        horizon_years=body.horizon_years,
        num_simulations=body.num_simulations,
        success_probability=result["success_probability"],
        failure_probability=result["failure_probability"],
        median_corpus=result["median_corpus"],
        p10_corpus=result["p10_corpus"],
        p25_corpus=result["p25_corpus"],
        p75_corpus=result["p75_corpus"],
        p90_corpus=result["p90_corpus"],
        required_monthly_sip=result["required_monthly_sip"],
        current_monthly_sip=body.monthly_sip,
        percentile_bands=result["percentile_bands"],
        histogram_data=result["histogram_data"],
        parameters=result["parameters"],
    )
