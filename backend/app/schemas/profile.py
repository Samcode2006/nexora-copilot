import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None = None
    full_name: str | None = None
    batch_year: int | None = None
    cgpa: Decimal | None = None
    backlogs: int | None = None
    branch: str | None = None
    created_at: datetime
    updated_at: datetime
