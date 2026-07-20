import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from rq import Queue
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.queue import get_queue
from app.models import Anomaly, Extraction, Report
from app.schemas.report import AnomalyOut, ExtractionOut, ReportDetail, ReportOut
from app.services import storage
from app.services.pipeline import process_report

router = APIRouter(tags=["reports"])

SUPPORTED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg"}


def get_queue_dependency() -> Queue:
    return get_queue()


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

    report = Report(id=report_id, filename=file.filename or "upload", storage_path=str(stored_path))
    db.add(report)
    db.commit()
    db.refresh(report)

    queue.enqueue(process_report, str(report.id))

    return report


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db)) -> ReportDetail:
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
