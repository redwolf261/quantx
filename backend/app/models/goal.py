"""Goal ORM model."""
import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text, Enum as SAEnum, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GoalType(str, enum.Enum):
    retirement = "retirement"
    home_purchase = "home_purchase"
    education = "education"
    emergency_fund = "emergency_fund"
    other = "other"


class GoalStatus(str, enum.Enum):
    active = "active"
    achieved = "achieved"
    paused = "paused"
    cancelled = "cancelled"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    goal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_type: Mapped[GoalType] = mapped_column(SAEnum(GoalType), default=GoalType.other)
    target_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    importance_score: Mapped[float] = mapped_column(Numeric(5, 2), default=5.0)

    # Computed / cached
    required_monthly_sip: Mapped[float | None] = mapped_column(Numeric(15, 2))
    current_success_probability: Mapped[float | None] = mapped_column(Numeric(5, 4))

    status: Mapped[GoalStatus] = mapped_column(SAEnum(GoalStatus), default=GoalStatus.active)
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="goals")
    simulation_results = relationship("SimulationResult", back_populates="goal")
    recommendations = relationship("Recommendation", back_populates="goal")
