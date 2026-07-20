import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONVariant, utcnow


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE")
    )
    schema_version: Mapped[str]
    data: Mapped[dict[str, Any]] = mapped_column(JSONVariant, default=dict)
    confidence: Mapped[dict[str, Any]] = mapped_column(JSONVariant, default=dict)
    validation_errors: Mapped[list[Any]] = mapped_column(JSONVariant, default=list)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
