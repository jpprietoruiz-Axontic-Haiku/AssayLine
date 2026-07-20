from app.demo.data import DEMO_REPORTS, DEMO_SPEC_PROFILES
from app.demo.seed import render_text_pdf, run_seed
from app.models import Anomaly, Report, SpecProfile
from app.services import classifier, document, storage


def test_render_text_pdf_roundtrips_embedded_text() -> None:
    pdf_bytes = render_text_pdf(DEMO_REPORTS[0]["text"])

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "demo.pdf"
        path.write_bytes(pdf_bytes)
        pages = document.extract_pages(path)

    assert len(pages) == 1
    assert "CERTIFICATE OF ANALYSIS" in pages[0].embedded_text
    assert "7.1" in pages[0].embedded_text


def test_demo_texts_self_classify_to_their_declared_report_type() -> None:
    for demo in DEMO_REPORTS:
        assert classifier.classify_report_type(demo["text"]) == demo["report_type"]


def test_run_seed_creates_expected_reports_specs_and_anomalies(
    db_session_factory, monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(storage, "_base_dir", lambda: tmp_path / "reports")
    db = db_session_factory()

    created = run_seed(db)

    assert len(created) == len(DEMO_REPORTS)
    assert db.query(SpecProfile).count() == len(DEMO_SPEC_PROFILES)
    assert db.query(Report).count() == len(DEMO_REPORTS)
    assert all(r.status == "extracted" for r in db.query(Report).all())

    # 2 of the 4 demo reports are deliberately out-of-spec (see app/demo/data.py)
    anomalies = db.query(Anomaly).all()
    assert len(anomalies) == 4
    severities = sorted(a.severity for a in anomalies)
    assert severities == ["critical", "critical", "warning", "warning"]
    db.close()


def test_run_seed_is_idempotent(db_session_factory, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(storage, "_base_dir", lambda: tmp_path / "reports")
    db = db_session_factory()

    run_seed(db)
    second_run_created = run_seed(db)

    assert second_run_created == []
    assert db.query(Report).count() == len(DEMO_REPORTS)
    assert db.query(SpecProfile).count() == len(DEMO_SPEC_PROFILES)
    db.close()
