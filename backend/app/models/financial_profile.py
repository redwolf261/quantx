"""Financial Profile ORM model."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Enum as SAEnum, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class RiskProfile(str, enum.Enum):
    conservative = "conservative"
    moderate = "moderate"
    aggressive = "aggressive"


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Personal
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    occupation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city_tier: Mapped[int] = mapped_column(Integer, default=1)

    # Income
    monthly_income: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    salary_growth_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.08)

    # Expenses
    monthly_expenses: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    inflation_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.06)

    # Assets
    total_savings: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    total_investments: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    equity_allocation: Mapped[float] = mapped_column(Numeric(5, 4), default=0.60)
    debt_allocation: Mapped[float] = mapped_column(Numeric(5, 4), default=0.40)

    # Liabilities
    total_loans: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    monthly_emi: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)

    # Risk
    risk_profile: Mapped[RiskProfile] = mapped_column(SAEnum(RiskProfile), default=RiskProfile.moderate)

    # Health score (cached computed value)
    health_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", back_populates="profile")