from app.models import SpecProfile
from tests.fixtures import SYNTHETIC_CERTIFICATE_TEXT, make_pdf_bytes


def _upload_certificate(client, db_session_factory, monkeypatch, ph_value=5.0):
    db = db_session_factory()
    db.add(
        SpecProfile(
            report_type="certificate_of_analysis",
            field="ph",
            min_value=6.5,
            max_value=7.5,
            unit=None,
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(
        "app.services.pipeline.run_extraction_agent",
        lambda *a, **k: {
            "fields": [{"name": "ph", "value": ph_value, "unit": None, "confidence": 0.9}]
        },
    )

    pdf_bytes = make_pdf_bytes(SYNTHETIC_CERTIFICATE_TEXT)
    response = client.post(
        "/reports", files={"file": ("certificate.pdf", pdf_bytes, "application/pdf")}
    )
    return response.json()["id"]


def test_list_reports_includes_anomaly_summary(client, db_session_factory, monkeypatch) -> None:
    report_id = _upload_certificate(client, db_session_factory, monkeypatch, ph_value=5.0)

    listing = client.get("/reports").json()

    item = next(r for r in listing if r["id"] == report_id)
    assert item["anomaly_count"] == 1
    assert item["has_critical_anomaly"] is True


def test_list_reports_can_filter_by_status(client, db_session_factory, monkeypatch) -> None:
    _upload_certificate(client, db_session_factory, monkeypatch, ph_value=7.0)

    listing = client.get("/reports", params={"status": "extracted"}).json()

    assert len(listing) == 1
    assert all(r["status"] == "extracted" for r in listing)


def test_get_original_document_serves_the_uploaded_pdf(
    client, db_session_factory, monkeypatch
) -> None:
    report_id = _upload_certificate(client, db_session_factory, monkeypatch, ph_value=7.0)

    response = client.get(f"/reports/{report_id}/original")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


def test_review_edit_and_approve_recomputes_anomalies(
    client, db_session_factory, monkeypatch
) -> None:
    report_id = _upload_certificate(client, db_session_factory, monkeypatch, ph_value=5.0)
    before = client.get(f"/reports/{report_id}").json()
    assert len(before["anomalies"]) == 1

    response = client.patch(
        f"/reports/{report_id}/review",
        json={"edits": {"ph": {"value": 7.0, "unit": None}}, "approve": True},
    )

    assert response.status_code == 200
    detail = response.json()
    assert detail["status"] == "reviewed"
    assert detail["extraction"]["data"]["ph"]["value"] == 7.0
    assert detail["anomalies"] == []  # corrected value is back in spec


def test_review_without_approve_keeps_status_and_saves_edits(
    client, db_session_factory, monkeypatch
) -> None:
    report_id = _upload_certificate(client, db_session_factory, monkeypatch, ph_value=5.0)

    response = client.patch(
        f"/reports/{report_id}/review",
        json={"edits": {"ph": {"value": 6.9, "unit": None}}, "approve": False},
    )

    detail = response.json()
    assert detail["status"] == "extracted"  # not yet approved
    assert detail["extraction"]["data"]["ph"]["value"] == 6.9


def test_export_json_includes_fields_and_anomalies(client, db_session_factory, monkeypatch) -> None:
    report_id = _upload_certificate(client, db_session_factory, monkeypatch, ph_value=5.0)

    response = client.post(f"/reports/{report_id}/export", params={"format": "json"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert body["fields"]["ph"]["value"] == 5.0
    assert body["anomalies"][0]["field"] == "ph"


def test_export_csv_contains_field_row(client, db_session_factory, monkeypatch) -> None:
    report_id = _upload_certificate(client, db_session_factory, monkeypatch, ph_value=7.0)

    response = client.post(f"/reports/{report_id}/export", params={"format": "csv"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "ph,7.0" in response.text.replace("\r\n", "\n")
