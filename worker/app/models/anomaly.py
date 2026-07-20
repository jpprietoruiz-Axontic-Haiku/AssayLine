import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE")
    )
    field: Mapped[str]
    value: Mapped[str | None] = mapped_column(default=None)
    expected_range: Mapped[str | None] = mapped_column(default=None)
    severity: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
