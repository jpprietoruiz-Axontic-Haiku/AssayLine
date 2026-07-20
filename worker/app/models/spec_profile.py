import uuid

from sqlalchemy import Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SpecProfile(Base):
    __tablename__ = "spec_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_type: Mapped[str]
    field: Mapped[str]
    min_value: Mapped[float | None] = mapped_column(Numeric, default=None)
    max_value: Mapped[float | None] = mapped_column(Numeric, default=None)
    unit: Mapped[str | None] = mapped_column(default=None)
