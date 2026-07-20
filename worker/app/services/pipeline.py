import logging
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models import Extraction, Report
from app.schemas.extraction import validate_fields
from app.services import classifier, document, storage, vision
from app.services.extraction_agent import run_extraction_agent

logger = logging.getLogger(__name__)


def process_report(report_id: str) -> None:
    """RQ job entrypoint: classify, transcribe (OCR/vision) and extract fields."""
    rid = uuid.UUID(report_id)
    session_factory = get_session_factory()
    with session_factory() as db:
        report = db.get(Report, rid)
        if report is None:
            logger.warning("report %s not found, skipping", report_id)
            return

        try:
            transcripts = _transcribe(db, report)
            _extract(db, report, transcripts)
        except Exception as exc:
            db.rollback()
            report.status = "failed"
            report.error_message = str(exc)[:1000]
            db.commit()
            raise


def _transcribe(db: Session, report: Report) -> list[str]:
    report_id = str(report.id)
    report.status = "processing"
    db.commit()

    pages = document.extract_pages(Path(report.storage_path))
    transcripts: list[str] = []
    for page in pages:
        storage.save_page_image(report_id, page.index, page.image_bytes, page.image_ext)
        text = page.embedded_text
        if len(text) < get_settings().min_embedded_text_chars:
            text = vision.transcribe_page(page.image_bytes, page.image_ext)
        storage.save_page_text(report_id, page.index, text)
        transcripts.append(text)

    report.report_type = classifier.classify_report_type("\n\n".join(transcripts))
    report.status = "transcribed"
    report.error_message = None
    db.commit()
    return transcripts


def _extract(db: Session, report: Report, transcripts: list[str]) -> None:
    report_type = report.report_type or "unknown"
    raw = run_extraction_agent(db, report_type, transcripts)
    raw_fields = raw.get("fields", []) if raw else []
    valid_fields, errors = validate_fields(raw_fields)

    if raw is None:
        errors = [*errors, {"field": "<extraction>", "errors": "agent did not submit a result"}]

    extraction = Extraction(
        report_id=report.id,
        schema_version=f"{report_type}.v1",
        data={
            name: {"value": field.value, "unit": field.unit}
            for name, field in valid_fields.items()
        },
        confidence={name: field.confidence for name, field in valid_fields.items()},
        validation_errors=errors,
    )
    db.add(extraction)
    report.status = "extracted"
    db.commit()
