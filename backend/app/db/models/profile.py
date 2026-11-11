import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ARRAY, CheckConstraint, DateTime, Integer, Numeric, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            "eligible_locations IS NULL OR cardinality(eligible_locations) BETWEEN 1 AND 20",
            name="ck_profiles_eligible_locations_count",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)  # = Supabase auth user id
    email: Mapped[str | None] = mapped_column(Text)
    full_name: Mapped[str | None] = mapped_column(Text)
    batch_year: Mapped[int | None] = mapped_column(Integer)
    cgpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    backlogs: Mapped[int | None] = mapped_column(Integer)
    branch: Mapped[str | None] = mapped_column(Text)
    eligible_locations: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
