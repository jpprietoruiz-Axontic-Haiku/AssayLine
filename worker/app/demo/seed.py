import logging
from pathlib import Path

import fitz
from sqlalchemy.orm import Session

from app.demo.data import DEMO_REPORTS, DEMO_SPEC_PROFILES
from app.models import Anomaly, Extraction, Report, SpecProfile
from app.services import document, storage
from app.services.anomaly_engine import detect_anomalies

logger = logging.getLogger(__name__)


def render_text_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
    overflow = page.insert_textbox(rect, text, fontsize=10, fontname="helv")
    if overflow < 0:
        raise ValueError("demo report text does not fit on a single page")
    return doc.tobytes()


def seed_spec_profiles(db: Session) -> int:
    created = 0
    for spec in DEMO_SPEC_PROFILES:
        exists = (
            db.query(SpecProfile)
            .filter(
                SpecProfile.report_type == spec["report_type"], SpecProfile.field == spec["field"]
            )
            .first()
        )
        if exists:
            continue
        db.add(
            SpecProfile(
                report_type=spec["report_type"],
                field=spec["field"],
                min_value=spec["min"],
                max_value=spec["max"],
                unit=spec["unit"],
            )
        )
        created += 1
    db.commit()
    return created


def seed_reports(db: Session) -> list[Report]:
    created: list[Report] = []
    for demo in DEMO_REPORTS:
        if db.query(Report).filter(Report.filename == demo["filename"]).first():
            continue

        report = Report(
            filename=demo["filename"],
            report_type=demo["report_type"],
            status="processing",
            storage_path="",
        )
        db.add(report)
        db.flush()  # assign report.id before we need it for storage paths

        report_id = str(report.id)
        pdf_bytes = render_text_pdf(demo["text"])
        stored_path = storage.save_original(report_id, demo["filename"], pdf_bytes)
        report.storage_path = str(stored_path)

        for page in document.extract_pages(Path(stored_path)):
            storage.save_page_image(report_id, page.index, page.image_bytes, page.image_ext)
            storage.save_page_text(report_id, page.index, page.embedded_text)

        extraction = Extraction(
            report_id=report.id,
            schema_version=f"{demo['report_type']}.v1",
            data={f["name"]: {"value": f["value"], "unit": f["unit"]} for f in demo["fields"]},
            confidence={f["name"]: f["confidence"] for f in demo["fields"]},
            validation_errors=[],
        )
        db.add(extraction)
        db.flush()

        for flag in detect_anomalies(db, demo["report_type"], extraction.data):
            db.add(
                Anomaly(
                    report_id=report.id,
                    field=flag.field,
                    value=flag.value,
                    expected_range=flag.expected_range,
                    severity=flag.severity,
                )
            )

        report.status = "extracted"
        created.append(report)

    db.commit()
    return created


def run_seed(db: Session) -> list[Report]:
    seed_spec_profiles(db)
    return seed_reports(db)
