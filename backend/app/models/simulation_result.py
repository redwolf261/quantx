"""Transaction, SimulationResult, Recommendation, RiskReport models."""
import uuid
import enum
from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, Text, Enum as SAEnum, UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Transaction ──────────────────────────────────────────────────────────────
class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="transactions")


# ── Simulation Result ─────────────────────────────────────────────────────────
class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), index=True, nullable=True)

    simulation_type: Mapped[str] = mapped_column(String(50), default="monte_carlo")
    num_simulations: Mapped[int] = mapped_column(Integer, default=10000)
    horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)

    success_probability: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    median_corpus: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    p10_corpus: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    p90_corpus: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    failure_probability: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)

    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="simulation_results")
    goal = relationship("Goal", back_populates="simulation_results")


# ── Recommendation ────────────────────────────────────────────────────────────
class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), index=True, nullable=True)

    recommendation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    current_probability: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    optimized_probability: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    recommended_sip: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    recommended_savings_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    recommended_retirement_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    explanation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    optimization_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="recommendations")
    goal = relationship("Goal", back_populates="recommendations")


# ── Risk Report ───────────────────────────────────────────────────────────────
class ScenarioType(str, enum.Enum):
    market_crash = "market_crash"
    inflation_spike = "inflation_spike"
    salary_loss = "salary_loss"
    medical_emergency = "medical_emergency"
    custom = "custom"


class RiskReport(Base):
    __tablename__ = "risk_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    scenario_type: Mapped[ScenarioType] = mapped_column(SAEnum(ScenarioType), nullable=False)
    scenario_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    base_success_prob: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    stressed_success_prob: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    probability_impact: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)

    base_median_corpus: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    stressed_median_corpus: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)

    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    result_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="risk_reports")