import csv
import io
import json
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from rq import Queue
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.queue import get_queue
from app.models import Anomaly, Extraction, Report, Review
from app.models.base import utcnow
from app.schemas.report import (
    AnomalyOut,
    ExtractionOut,
    ReportDetail,
    ReportListItem,
    ReportOut,
)
from app.schemas.review import ReviewRequest
from app.services import storage
from app.services.anomaly_engine import detect_anomalies
from app.services.pipeline import process_report

router = APIRouter(tags=["reports"])

SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}
_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def get_queue_dependency() -> Queue:
    return get_queue()


def _load_detail(db: Session, report_id: uuid.UUID) -> ReportDetail:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(404, "report not found")

    extraction = (
        db.query(Extraction)
        .filter(Extraction.report_id == report_id)
        .order_by(Extraction.created_at.desc())
        .first()
    )
    anomalies = db.query(Anomaly).filter(Anomaly.report_id == report_id).all()

    detail = ReportDetail.model_validate(report)
    detail.extraction = ExtractionOut.model_validate(extraction) if extraction else None
    detail.anomalies = [AnomalyOut.model_validate(a) for a in anomalies]
    return detail


@router.post("/reports", response_model=ReportOut, status_code=201)
def create_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    queue: Queue = Depends(get_queue_dependency),
) -> Report:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(415, f"unsupported file type: {suffix}")

    settings = get_settings()
    content = file.file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"file exceeds {settings.max_upload_mb}MB limit")

    report_id = uuid.uuid4()
    stored_path = storage.save_original(str(report_id), file.filename or "upload", content)

    report = Report(
        id=report_id, filename=file.filename or "upload", storage_path=str(stored_path)
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    queue.enqueue(process_report, str(report.id))

    return report


@router.get("/reports", response_model=list[ReportListItem])
def list_reports(status: str | None = None, db: Session = Depends(get_db)) -> list[ReportListItem]:
    query = db.query(Report).order_by(Report.uploaded_at.desc())
    if status:
        query = query.filter(Report.status == status)
    reports = query.all()

    counts = dict(
        db.query(Anomaly.report_id, func.count(Anomaly.id)).group_by(Anomaly.report_id).all()
    )
    critical_ids = {
        row[0]
        for row in db.query(Anomaly.report_id).filter(Anomaly.severity == "critical").distinct()
    }

    return [
        ReportListItem(
            **ReportOut.model_validate(r).model_dump(),
            anomaly_count=counts.get(r.id, 0),
            has_critical_anomaly=r.id in critical_ids,
        )
        for r in reports
    ]


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)) -> ReportDetail:
    return _load_detail(db, report_id)


@router.get("/reports/{report_id}/original")
def get_original_document(report_id: uuid.UUID, db: Session = Depends(get_db)) -> FileResponse:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(404, "report not found")

    path = Path(report.storage_path)
    if not path.exists():
        raise HTTPException(404, "original file not found in storage")

    media_type = _MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type, filename=report.filename)


@router.patch("/reports/{report_id}/review", response_model=ReportDetail)
def review_report(
    report_id: uuid.UUID, body: ReviewRequest, db: Session = Depends(get_db)
) -> ReportDetail:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(404, "report not found")

    extraction = (
        db.query(Extraction)
        .filter(Extraction.report_id == report_id)
        .order_by(Extraction.created_at.desc())
        .first()
    )
    if extraction is None:
        raise HTTPException(409, "report has no extraction to review yet")

    data = dict(extraction.data)
    for field_name, edit in body.edits.items():
        existing = data.get(field_name, {})
        data[field_name] = {
            "value": edit.value,
            "unit": edit.unit if edit.unit is not None else existing.get("unit"),
        }
    extraction.data = data

    review = db.query(Review).filter(Review.report_id == report_id).first()
    if review is None:
        review = Review(report_id=report_id, reviewer_edits={})
        db.add(review)
    combined_edits = dict(review.reviewer_edits)
    combined_edits.update({name: edit.model_dump() for name, edit in body.edits.items()})
    review.reviewer_edits = combined_edits

    if body.approve:
        review.approved_at = utcnow()
        report.status = "reviewed"

        # human corrections can change which fields are out of spec: re-flag
        # from scratch against the corrected data rather than leaving stale
        # anomalies from the original (uncorrected) extraction.
        db.query(Anomaly).filter(Anomaly.report_id == report_id).delete()
        for flag in detect_anomalies(db, report.report_type or "unknown", data):
            db.add(
                Anomaly(
                    report_id=report_id,
                    field=flag.field,
                    value=flag.value,
                    expected_range=flag.expected_range,
                    severity=flag.severity,
                )
            )

    db.commit()
    return _load_detail(db, report_id)


@router.post("/reports/{report_id}/export")
def export_report(
    report_id: uuid.UUID,
    format: Literal["json", "csv"] = "json",
    db: Session = Depends(get_db),
) -> Response:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(404, "report not found")

    extraction = (
        db.query(Extraction)
        .filter(Extraction.report_id == report_id)
        .order_by(Extraction.created_at.desc())
        .first()
    )
    if extraction is None:
        raise HTTPException(409, "report has no extraction to export yet")
    anomalies = db.query(Anomaly).filter(Anomaly.report_id == report_id).all()
    stem = Path(report.filename).stem

    if format == "csv":
        return _export_csv(extraction, anomalies, stem)
    return _export_json(report, extraction, anomalies, stem)


def _export_csv(extraction: Extraction, anomalies: list[Anomaly], stem: str) -> Response:
    anomaly_by_field = {a.field: a for a in anomalies}
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["field", "value", "unit", "confidence", "anomaly_severity", "expected_range"])
    for field_name, payload in extraction.data.items():
        anomaly = anomaly_by_field.get(field_name)
        writer.writerow(
            [
                field_name,
                payload.get("value"),
                payload.get("unit") or "",
                extraction.confidence.get(field_name, ""),
                anomaly.severity if anomaly else "",
                anomaly.expected_range if anomaly else "",
            ]
        )
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{stem}_export.csv"'},
    )


def _export_json(
    report: Report, extraction: Extraction, anomalies: list[Anomaly], stem: str
) -> Response:
    payload = {
        "report": {
            "id": str(report.id),
            "filename": report.filename,
            "report_type": report.report_type,
            "status": report.status,
        },
        "fields": extraction.data,
        "confidence": extraction.confidence,
        "anomalies": [
            {
                "field": a.field,
                "value": a.value,
                "expected_range": a.expected_range,
                "severity": a.severity,
            }
            for a in anomalies
        ],
    }
    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{stem}_export.json"'},
    )
