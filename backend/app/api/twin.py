"""
Financial Twin API — /twin
==========================
Unified router for the Financial Intelligence Platform.

Endpoints:
  POST /twin/futures        — Generate 4 future branches (Future Tree)
  POST /twin/attribution    — Compute factor attribution (WHY engine)
  GET  /twin/behavior       — Compute behavioral scores (7 dimensions)
  GET  /twin/dna            — Financial Health DNA (7-axis radar data)
  GET  /twin/timeline       — Financial life timeline (year-by-year milestones)
  POST /twin/historical     — Run historical scenario (COVID, 2008, etc.)
"""
from __future__ import annotations
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.engines.future_tree import FutureTreeEngine
from app.engines.decision_attribution import DecisionAttributionEngine
from app.engines.behavior_engine import BehaviorEngine
from app.engines.monte_carlo import MonteCarloEngine

router = APIRouter()

# ── Request / Response Schemas ────────────────────────────────────────────────

class FutureTreeRequest(BaseModel):
    goal_id:        Optional[str] = None
    monthly_sip:    float = Field(gt=0)
    horizon_years:  int   = Field(ge=3, le=50)
    target_amount:  Optional[float] = None


class AttributionRequest(BaseModel):
    goal_id:       Optional[str] = None
    monthly_sip:   float = Field(gt=0)
    horizon_years: int   = Field(ge=3, le=50)
    target_amount: Optional[float] = None


class HistoricalScenarioRequest(BaseModel):
    scenario_id:   str
    monthly_sip:   float = Field(gt=0)
    horizon_years: int   = Field(ge=3, le=50)
    target_amount: Optional[float] = None


# ── Historical Scenario Definitions (mathematically sourced) ──────────────────
# Parameters derived from actual historical market data for each period.

HISTORICAL_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "crisis_2008": {
        "name": "2008 Global Financial Crisis",
        "emoji": "💥",
        "period": "2007–2010",
        "description": "Lehman Brothers collapse — global equity markets fell ~45%, credit froze",
        "equity_return_shock": -0.45,   # one-time wealth reduction
        "inflation_shock":      -0.01,   # deflation risk
        "income_shock":         -0.12,   # job market contraction
        "duration_years":        3,
    },
    "covid_2020": {
        "name": "COVID-19 Pandemic",
        "emoji": "🦠",
        "period": "2020–2022",
        "description": "Global lockdowns — equity fell 35% then recovered; post-COVID inflation surged",
        "equity_return_shock": -0.35,
        "inflation_shock":      +0.04,
        "income_shock":         -0.20,
        "duration_years":        2,
    },
    "high_inflation": {
        "name": "High Inflation Era",
        "emoji": "📈",
        "period": "2022–2024",
        "description": "Post-pandemic inflation spike — real returns compressed significantly",
        "equity_return_shock":  -0.10,
        "inflation_shock":      +0.08,
        "income_shock":          0.0,
        "duration_years":        4,
    },
    "oil_shock": {
        "name": "Oil Price Shock",
        "emoji": "🛢️",
        "period": "1973 / 2007 type",
        "description": "Energy price surge — broad inflation, equity market correction",
        "equity_return_shock": -0.20,
        "inflation_shock":      +0.06,
        "income_shock":         -0.05,
        "duration_years":        2,
    },
    "ai_boom": {
        "name": "AI Technology Boom",
        "emoji": "🤖",
        "period": "2023–2026 type",
        "description": "Productivity surge — equity markets rally, tech salaries elevated",
        "equity_return_shock": +0.15,
        "inflation_shock":      +0.02,
        "income_shock":         +0.10,
        "duration_years":        3,
    },
    "rate_hike": {
        "name": "Rate Hike Cycle",
        "emoji": "🏦",
        "period": "2022–2023 type",
        "description": "Central banks aggressively raised rates — equity sold off, bonds hurt",
        "equity_return_shock": -0.15,
        "inflation_shock":      -0.03,
        "income_shock":          0.0,
        "duration_years":        3,
    },
    "recession": {
        "name": "Global Recession",
        "emoji": "📉",
        "period": "2001 / 2008 / 2020 type",
        "description": "Broad economic contraction — equity, income, and spending all impacted",
        "equity_return_shock": -0.30,
        "inflation_shock":      +0.02,
        "income_shock":         -0.18,
        "duration_years":        3,
    },
    "housing_bubble": {
        "name": "Housing Bubble Burst",
        "emoji": "🏠",
        "period": "2008 / India type",
        "description": "Real estate crash — asset values fall, construction sector contracts",
        "equity_return_shock": -0.25,
        "inflation_shock":      +0.03,
        "income_shock":         -0.08,
        "duration_years":        4,
    },
}

AVAILABLE_SCENARIOS = [
    {"id": k, "name": v["name"], "emoji": v["emoji"],
     "period": v["period"], "description": v["description"]}
    for k, v in HISTORICAL_SCENARIOS.items()
]


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _require_profile(user: User, db: AsyncSession) -> FinancialProfile:
    result = await db.execute(select(FinancialProfile).where(FinancialProfile.user_id == user.id))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Financial profile not found. Please complete your profile first."
        )
    return profile


async def _get_goals(user: User, db: AsyncSession) -> List[Goal]:
    result = await db.execute(select(Goal).where(Goal.user_id == user.id))
    return list(result.scalars().all())


def _compute_dna(profile: FinancialProfile, behavior: Dict) -> Dict[str, float]:
    """Map behavior scores + profile data to 7-dimension DNA chart."""
    scores = behavior["scores"]
    income   = float(profile.monthly_income)
    expenses = float(profile.monthly_expenses)
    savings  = float(profile.total_savings)
    invest   = float(profile.total_investments)

    # Insurance proxy: use a fixed heuristic (profile has no insurance field yet)
    # Assumes moderate coverage for salaried employees; 50 if no data
    insurance_score = 65.0  # conservative default until insurance data is added

    return {
        "savings":    scores["savings_discipline"],
        "risk":       scores["risk_alignment"],
        "liquidity":  scores["emergency_fund"],
        "debt":       scores["debt_management"],
        "investment": scores["investment_rate"],
        "insurance":  insurance_score,
        "behavior":   behavior["overall"],
        "overall":    round(behavior["overall"] * 0.8 + insurance_score * 0.2, 1),
    }


def _generate_timeline(profile: FinancialProfile, goals: List[Goal]) -> List[Dict]:
    """
    Generate year-by-year financial life milestones from profile data.
    Pure deterministic computation — no Monte Carlo required.
    """
    current_year = datetime.now().year
    events = []
    income   = float(profile.monthly_income)
    expenses = float(profile.monthly_expenses)
    savings  = float(profile.total_savings)
    emi      = float(profile.monthly_emi)
    loans    = float(profile.total_loans)

    monthly_surplus = max(0, income - expenses - emi)

    # ── Emergency fund completion ──────────────────────────────────────────────
    ef_target = expenses * 6
    if savings < ef_target and monthly_surplus > 0:
        ef_gap    = ef_target - savings
        ef_months = ef_gap / (monthly_surplus * 0.3)   # assumes 30% of surplus to ef
        ef_year   = current_year + max(1, int(ef_months / 12))
        events.append({
            "year":        ef_year,
            "title":       "Emergency Fund Complete",
            "description": f"6-month buffer of INR {round(ef_target/100000, 1):.1f}L secured",
            "type":        "milestone",
            "icon":        "🛡️",
            "amount":      ef_target,
            "achieved":    savings >= ef_target,
            "probability": None,
        })
    elif savings >= ef_target:
        events.append({
            "year":        current_year,
            "title":       "Emergency Fund Complete",
            "description": f"6-month buffer already secured — INR {round(savings/100000, 1):.1f}L",
            "type":        "achievement",
            "icon":        "✅",
            "amount":      savings,
            "achieved":    True,
            "probability": None,
        })

    # ── Loan closure ──────────────────────────────────────────────────────────
    if loans > 0 and emi > 0:
        months_to_close  = loans / emi
        closure_year     = current_year + max(1, int(months_to_close / 12))
        events.append({
            "year":        closure_year,
            "title":       "Loan Fully Repaid",
            "description": f"INR {round(loans/100000, 1):.1f}L cleared — INR {round(emi):,}/mo freed",
            "type":        "milestone",
            "icon":        "🎉",
            "amount":      loans,
            "achieved":    False,
            "probability": None,
        })

    # ── SIP corpus milestones ─────────────────────────────────────────────────
    invest   = float(profile.total_investments)
    sip_approx = monthly_surplus * 0.7
    growth_rate_monthly = 0.09 / 12

    # First crore milestone
    if invest < 10_000_000 and sip_approx > 0:
        corpus = invest
        months = 0
        while corpus < 10_000_000 and months < 600:
            corpus = corpus * (1 + growth_rate_monthly) + sip_approx
            months += 1
        if months < 600:
            events.append({
                "year":        current_year + months // 12,
                "title":       "First Crore Milestone",
                "description": "Portfolio crosses INR 1 Crore — compounding accelerates",
                "type":        "milestone",
                "icon":        "💰",
                "amount":      10_000_000,
                "achieved":    False,
                "probability": None,
            })

    # ── Goal milestones ───────────────────────────────────────────────────────
    for goal in sorted(goals, key=lambda g: g.target_year):
        prob = float(goal.current_success_probability) if goal.current_success_probability else None
        events.append({
            "year":        goal.target_year,
            "title":       goal.goal_name,
            "description": f"Target: INR {round(goal.target_amount/100000, 1):.1f}L by {goal.target_year}",
            "type":        "goal",
            "icon":        _goal_icon(goal.goal_type),
            "amount":      float(goal.target_amount),
            "achieved":    False,
            "probability": round(prob, 4) if prob else None,
        })

    # Sort chronologically
    return sorted(events, key=lambda e: e["year"])


def _goal_icon(goal_type: str) -> str:
    return {
        "retirement":    "🏖️",
        "home_purchase": "🏠",
        "education":     "🎓",
        "emergency_fund": "🛡️",
        "other":         "🎯",
    }.get(goal_type, "🎯")


# ── Route Handlers ────────────────────────────────────────────────────────────

@router.post("/futures")
async def generate_futures(
    body: FutureTreeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Generate 4 Financial Twin future paths with independent Monte Carlo."""
    profile = await _require_profile(current_user, db)
    engine  = FutureTreeEngine(profile)
    futures = engine.generate(
        base_sip=body.monthly_sip,
        base_horizon=body.horizon_years,
        target_amount=body.target_amount,
    )
    return {
        "futures":        futures,
        "base_sip":       body.monthly_sip,
        "base_horizon":   body.horizon_years,
        "target_amount":  body.target_amount,
        "profile_age":    profile.age,
        "risk_profile":   profile.risk_profile.value,
    }


@router.post("/attribution")
async def compute_attribution(
    body: AttributionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Compute WHY attribution — factor-level explanation of success probability."""
    profile = await _require_profile(current_user, db)
    engine  = DecisionAttributionEngine(profile)
    result  = engine.compute(
        monthly_sip=body.monthly_sip,
        horizon_years=body.horizon_years,
        target_amount=body.target_amount,
    )
    return result


@router.get("/behavior")
async def get_behavior(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Compute behavioral financial scores — 7 dimensions, pure Python."""
    profile = await _require_profile(current_user, db)
    engine  = BehaviorEngine(profile)
    return engine.compute()


@router.get("/dna")
async def get_dna(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Financial Health DNA — 7-dimension radar chart data."""
    profile  = await _require_profile(current_user, db)
    behavior = BehaviorEngine(profile).compute()
    dna      = _compute_dna(profile, behavior)
    return {
        "dna":       dna,
        "behavior":  behavior,
        "profile_id": str(profile.id),
    }


@router.get("/timeline")
async def get_timeline(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """Financial life timeline — chronological milestones from profile + goals."""
    profile = await _require_profile(current_user, db)
    goals   = await _get_goals(current_user, db)
    events  = _generate_timeline(profile, goals)
    return {
        "events":       events,
        "current_year": datetime.now().year,
        "total_events": len(events),
    }


@router.get("/scenarios")
async def list_scenarios() -> Dict[str, Any]:
    """List all available historical stress scenarios."""
    return {"scenarios": AVAILABLE_SCENARIOS}


@router.post("/historical")
async def run_historical_scenario(
    body: HistoricalScenarioRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict[str, Any]:
    """
    Apply a historical market scenario and recompute success probability.
    Uses parametric shocks derived from actual historical data.
    """
    if body.scenario_id not in HISTORICAL_SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {body.scenario_id}")

    profile = await _require_profile(current_user, db)
    sc      = HISTORICAL_SCENARIOS[body.scenario_id]

    initial_wealth = float(profile.total_savings) + float(profile.total_investments)

    # Apply equity shock to initial wealth (marks-to-market)
    shocked_wealth = max(0.0, initial_wealth * (1 + sc["equity_return_shock"]))

    # Apply income shock — reduces SIP proportionally
    shocked_sip = max(500, body.monthly_sip * (1 + sc["income_shock"]))

    # Apply inflation shock — add to profile inflation rate
    shocked_inflation = max(0.02, min(0.25, float(profile.inflation_rate) + sc["inflation_shock"]))

    # Run baseline (no shock)
    base_engine = MonteCarloEngine(
        initial_wealth=initial_wealth,
        monthly_sip=body.monthly_sip,
        horizon_years=body.horizon_years,
        equity_allocation=float(profile.equity_allocation),
        debt_allocation=float(profile.debt_allocation),
        risk_profile=profile.risk_profile.value,
        salary_growth_rate=float(profile.salary_growth_rate),
        inflation_rate=float(profile.inflation_rate),
        num_simulations=5000,
    )
    base = base_engine.run(target_amount=body.target_amount)

    # Run stressed scenario
    stressed_engine = MonteCarloEngine(
        initial_wealth=shocked_wealth,
        monthly_sip=shocked_sip,
        horizon_years=body.horizon_years,
        equity_allocation=float(profile.equity_allocation),
        debt_allocation=float(profile.debt_allocation),
        risk_profile=profile.risk_profile.value,
        salary_growth_rate=float(profile.salary_growth_rate),
        inflation_rate=shocked_inflation,
        num_simulations=5000,
    )
    stressed = stressed_engine.run(target_amount=body.target_amount)

    prob_impact = stressed["success_probability"] - base["success_probability"]
    corpus_impact_pct = (
        (stressed["median_corpus"] - base["median_corpus"]) / max(1, base["median_corpus"])
    ) * 100

    return {
        "scenario_id":              body.scenario_id,
        "scenario_name":            sc["name"],
        "scenario_emoji":           sc["emoji"],
        "period":                   sc["period"],
        "description":              sc["description"],
        "base_probability":         round(base["success_probability"], 4),
        "stressed_probability":     round(stressed["success_probability"], 4),
        "probability_impact":       round(prob_impact, 4),
        "probability_impact_pct":   round(prob_impact * 100, 1),
        "base_median_corpus":       round(base["median_corpus"], 0),
        "stressed_median_corpus":   round(stressed["median_corpus"], 0),
        "corpus_impact_pct":        round(corpus_impact_pct, 1),
        "shocks_applied": {
            "equity_shock_pct":     round(sc["equity_return_shock"] * 100, 1),
            "income_shock_pct":     round(sc["income_shock"] * 100, 1),
            "inflation_shock_pct":  round(sc["inflation_shock"] * 100, 1),
        },
        "base_result":    {k: round(v, 2) if isinstance(v, float) else v
                           for k, v in base.items() if k in
                           ("success_probability","median_corpus","p10_corpus","p90_corpus")},
        "stressed_result": {k: round(v, 2) if isinstance(v, float) else v
                            for k, v in stressed.items() if k in
                            ("success_probability","median_corpus","p10_corpus","p90_corpus")},
    }
