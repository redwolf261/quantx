"""Pydantic schemas for Auth, User, Profile, Goals, Simulation, Stress, Optimization, Explain."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(default="customer", pattern="^(customer|rm|admin)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    role: str


# ── User ──────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Financial Profile ─────────────────────────────────────────────────────────
class ProfileCreate(BaseModel):
    age: int = Field(ge=18, le=100)
    occupation: Optional[str] = None
    city: Optional[str] = None
    city_tier: int = Field(default=1, ge=1, le=3)

    monthly_income: float = Field(gt=0)
    salary_growth_rate: float = Field(default=0.08, ge=0, le=0.5)

    monthly_expenses: float = Field(gt=0)
    inflation_rate: float = Field(default=0.06, ge=0, le=0.3)

    total_savings: float = Field(default=0.0, ge=0)
    total_investments: float = Field(default=0.0, ge=0)
    equity_allocation: float = Field(default=0.60, ge=0, le=1)
    debt_allocation: float = Field(default=0.40, ge=0, le=1)

    total_loans: float = Field(default=0.0, ge=0)
    monthly_emi: float = Field(default=0.0, ge=0)

    risk_profile: str = Field(default="moderate", pattern="^(conservative|moderate|aggressive)$")

    @field_validator("equity_allocation", "debt_allocation")
    @classmethod
    def validate_allocation(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Allocation must be between 0 and 1")
        return v


class ProfileUpdate(ProfileCreate):
    pass


class ProfileOut(ProfileCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    health_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Goals ─────────────────────────────────────────────────────────────────────
class GoalCreate(BaseModel):
    goal_name: str = Field(min_length=1, max_length=255)
    goal_type: str = Field(default="other", pattern="^(retirement|home_purchase|education|emergency_fund|other)$")
    target_amount: float = Field(gt=0)
    target_year: int = Field(ge=2025, le=2100)
    priority: int = Field(default=1, ge=1, le=5)
    importance_score: float = Field(default=5.0, ge=1, le=10)
    notes: Optional[str] = None


class GoalOut(GoalCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    required_monthly_sip: Optional[float] = None
    current_success_probability: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Simulation ────────────────────────────────────────────────────────────────
class SimulationRequest(BaseModel):
    goal_id: Optional[uuid.UUID] = None
    horizon_years: int = Field(ge=1, le=50)
    monthly_sip: float = Field(ge=0)
    initial_wealth: Optional[float] = None  # overrides profile if set
    target_amount: Optional[float] = None   # overrides goal if set
    num_simulations: int = Field(default=10000, ge=1000, le=100000)


class SimulationResult(BaseModel):
    simulation_id: uuid.UUID
    goal_id: Optional[uuid.UUID]
    horizon_years: int
    num_simulations: int

    success_probability: float
    failure_probability: float
    median_corpus: float
    p10_corpus: float
    p25_corpus: float
    p75_corpus: float
    p90_corpus: float

    required_monthly_sip: float
    current_monthly_sip: float

    # Time-series data for charts (list of yearly snapshots)
    percentile_bands: List[Dict[str, Any]]  # [{year, p10, p25, p50, p75, p90}]
    histogram_data: List[Dict[str, Any]]    # [{bucket, count}]

    parameters: Dict[str, Any]


# ── Stress Test ───────────────────────────────────────────────────────────────
class StressTestRequest(BaseModel):
    goal_id: Optional[uuid.UUID] = None
    horizon_years: int = Field(ge=1, le=50)
    monthly_sip: float = Field(ge=0)
    scenarios: List[str] = Field(
        default=["market_crash", "inflation_spike", "salary_loss", "medical_emergency"],
        min_length=1,
    )


class ScenarioResult(BaseModel):
    scenario: str
    scenario_label: str
    base_success_probability: float
    stressed_success_probability: float
    probability_impact: float
    base_median_corpus: float
    stressed_median_corpus: float
    corpus_impact_pct: float
    risk_level: str  # low | medium | high | critical
    percentile_bands: List[Dict[str, Any]]


class StressTestResult(BaseModel):
    goal_id: Optional[uuid.UUID]
    horizon_years: int
    base_result: Dict[str, Any]
    scenarios: List[ScenarioResult]


# ── Optimization ──────────────────────────────────────────────────────────────
class OptimizationRequest(BaseModel):
    goal_id: Optional[uuid.UUID] = None
    horizon_years: int = Field(ge=1, le=50)
    target_probability: float = Field(default=0.80, ge=0.5, le=0.99)

    # Bounds for decision variables
    min_sip: float = Field(default=500, ge=0)
    max_sip: float = Field(default=200000, le=1000000)
    min_retirement_age: int = Field(default=50, ge=40)
    max_retirement_age: int = Field(default=70, le=80)

    constraints: Optional[Dict[str, Any]] = None


class OptimizationResult(BaseModel):
    goal_id: Optional[uuid.UUID]
    current_probability: float
    optimized_probability: float
    improvement: float

    current_sip: float
    recommended_sip: float
    sip_increase: float

    recommended_savings_rate: float
    recommended_retirement_age: Optional[int] = None

    optimization_path: List[Dict[str, Any]]  # convergence data
    parameters: Dict[str, Any]


# ── Explainer ─────────────────────────────────────────────────────────────────
class ExplainRequest(BaseModel):
    context_type: str = Field(
        pattern="^(simulation|stress_test|optimization|goal_status|portfolio)$"
    )
    structured_data: Dict[str, Any]
    goal_name: Optional[str] = None
    user_name: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    key_insights: List[str]
    action_items: List[str]
    model_used: str
    is_fallback: bool = False


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardResponse(BaseModel):
    user: UserOut
    profile: Optional[ProfileOut] = None
    goals: List[GoalOut] = []
    net_worth: float = 0.0
    monthly_surplus: float = 0.0
    health_score: float = 0.0
    goals_summary: Dict[str, Any] = {}
    latest_simulation: Optional[Dict[str, Any]] = None
    recommendations_count: int = 0


# ── RM Dashboard ──────────────────────────────────────────────────────────────
class CustomerSummary(BaseModel):
    user: UserOut
    profile: Optional[ProfileOut] = None
    health_score: float = 0.0
    net_worth: float = 0.0
    goals_count: int = 0
    avg_success_probability: float = 0.0
    risk_level: str = "medium"
    discussion_points: List[str] = []
    last_active: Optional[datetime] = None
