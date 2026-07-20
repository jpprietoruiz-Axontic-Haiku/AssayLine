import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, JSONVariant


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE")
    )
    reviewer_edits: Mapped[dict[str, Any]] = mapped_column(JSONVariant, default=dict)
    approved_at: Mapped[datetime | None] = mapped_column(default=None)
