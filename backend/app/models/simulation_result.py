"""Transaction, SimulationResult, Recommendation, RiskReport models."""
import uuid
import enum
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, Text, ARRAY, Enum as SAEnum, UUID, JSON
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
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="transactions")


# ── Simulation Result ─────────────────────────────────────────────────────────
class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"), index=True)

    simulation_type: Mapped[str] = mapped_column(String(50), default="monte_carlo")
    num_simulations: Mapped[int] = mapped_column(Integer, default=10000)
    horizon_years: Mapped[int] = mapped_column(Integer, nullable=False)

    success_probability: Mapped[float | None] = mapped_column(Numeric(5, 4))
    median_corpus: Mapped[float | None] = mapped_column(Numeric(20, 2))
    p10_corpus: Mapped[float | None] = mapped_column(Numeric(20, 2))
    p90_corpus: Mapped[float | None] = mapped_column(Numeric(20, 2))
    failure_probability: Mapped[float | None] = mapped_column(Numeric(5, 4))

    result_data: Mapped[dict | None] = mapped_column(JSON)
    parameters: Mapped[dict | None] = mapped_column(JSON)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="simulation_results")
    goal = relationship("Goal", back_populates="simulation_results")


# ── Recommendation ────────────────────────────────────────────────────────────
class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("goals.id", ondelete="SET NULL"))

    recommendation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    current_probability: Mapped[float | None] = mapped_column(Numeric(5, 4))
    optimized_probability: Mapped[float | None] = mapped_column(Numeric(5, 4))
    recommended_sip: Mapped[float | None] = mapped_column(Numeric(15, 2))
    recommended_savings_rate: Mapped[float | None] = mapped_column(Numeric(5, 4))
    recommended_retirement_age: Mapped[int | None] = mapped_column(Integer)

    explanation_text: Mapped[str | None] = mapped_column(Text)
    explanation_model: Mapped[str | None] = mapped_column(String(100))
    optimization_data: Mapped[dict | None] = mapped_column(JSON)

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
    scenario_params: Mapped[dict | None] = mapped_column(JSON)

    base_success_prob: Mapped[float | None] = mapped_column(Numeric(5, 4))
    stressed_success_prob: Mapped[float | None] = mapped_column(Numeric(5, 4))
    probability_impact: Mapped[float | None] = mapped_column(Numeric(5, 4))

    base_median_corpus: Mapped[float | None] = mapped_column(Numeric(20, 2))
    stressed_median_corpus: Mapped[float | None] = mapped_column(Numeric(20, 2))

    risk_level: Mapped[str | None] = mapped_column(String(20))
    result_data: Mapped[dict | None] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="risk_reports")
