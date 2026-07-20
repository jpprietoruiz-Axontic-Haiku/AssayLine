import logging
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models import Report
from app.services import classifier, document, storage, vision

logger = logging.getLogger(__name__)


def process_report(report_id: str) -> None:
    """RQ job entrypoint: classify report type and transcribe pages (OCR/vision)."""
    rid = uuid.UUID(report_id)
    session_factory = get_session_factory()
    with session_factory() as db:
        report = db.get(Report, rid)
        if report is None:
            logger.warning("report %s not found, skipping", report_id)
            return

        try:
            report.status = "processing"
            db.commit()

            pages = document.extract_pages(Path(report.storage_path))
            transcripts = []
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
        except Exception as exc:
            db.rollback()
            report.status = "failed"
            report.error_message = str(exc)[:1000]
            db.commit()
            raise
