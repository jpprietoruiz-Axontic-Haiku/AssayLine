import uuid
from datetime import datetime

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    filename: Mapped[str]
    report_type: Mapped[str | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="uploaded")
    storage_path: Mapped[str]
    error_message: Mapped[str | None] = mapped_column(default=None)
    uploaded_at: Mapped[datetime] = mapped_column(default=utcnow)
