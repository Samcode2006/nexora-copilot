import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None = None
    full_name: str | None = None
    batch_year: int | None = None
    cgpa: Decimal | None = None
    backlogs: int | None = None
    branch: str | None = None
    eligible_locations: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    batch_year: int | None = Field(default=None, ge=2000, le=2100)
    cgpa: Decimal | None = Field(default=None, ge=0, le=10, max_digits=4, decimal_places=2)
    backlogs: int | None = Field(default=None, ge=0)
    branch: str | None = Field(default=None, min_length=1, max_length=120)
    eligible_locations: list[str] | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("eligible_locations")
    @classmethod
    def validate_locations(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and any(not item.strip() or len(item) > 100 for item in value):
            raise ValueError("locations must contain 1 to 100 characters")
        return value
