import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ReportStatus(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    EXTRACTED = "extracted"
    REVIEWED = "reviewed"
    FAILED = "failed"


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    report_type: str | None
    status: str
    uploaded_at: datetime
    error_message: str | None


class ExtractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schema_version: str
    data: dict[str, Any]
    confidence: dict[str, Any]
    validation_errors: list[Any]
    created_at: datetime


class AnomalyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field: str
    value: str | None
    expected_range: str | None
    severity: str


class ReportDetail(ReportOut):
    extraction: ExtractionOut | None = None
    anomalies: list[AnomalyOut] = []


class ReportListItem(ReportOut):
    anomaly_count: int = 0
    has_critical_anomaly: bool = False
