from tests.fixtures import SYNTHETIC_CERTIFICATE_TEXT, make_pdf_bytes


def test_extraction_validation_errors_are_reported_per_field_without_dropping_valid_ones(
    client, monkeypatch
) -> None:
    monkeypatch.setattr(
        "app.services.pipeline.run_extraction_agent",
        lambda *a, **k: {
            "fields": [
                {"name": "ph", "value": 7.2, "unit": None, "confidence": 0.9},
                {"name": "pureza", "value": 99.5, "unit": "%", "confidence": 1.5},  # out of range
            ]
        },
    )

    pdf_bytes = make_pdf_bytes(SYNTHETIC_CERTIFICATE_TEXT)
    response = client.post(
        "/reports", files={"file": ("certificate.pdf", pdf_bytes, "application/pdf")}
    )
    report_id = response.json()["id"]

    detail = client.get(f"/reports/{report_id}").json()
    assert detail["status"] == "extracted"
    assert detail["extraction"]["data"]["ph"]["value"] == 7.2
    assert "pureza" not in detail["extraction"]["data"]
    assert any(e["field"] == "pureza" for e in detail["extraction"]["validation_errors"])


def test_extraction_degrades_gracefully_when_agent_never_submits(client, monkeypatch) -> None:
    monkeypatch.setattr("app.services.pipeline.run_extraction_agent", lambda *a, **k: None)

    pdf_bytes = make_pdf_bytes(SYNTHETIC_CERTIFICATE_TEXT)
    response = client.post(
        "/reports", files={"file": ("certificate.pdf", pdf_bytes, "application/pdf")}
    )
    report_id = response.json()["id"]

    detail = client.get(f"/reports/{report_id}").json()
    assert detail["status"] == "extracted"
    assert detail["extraction"]["data"] == {}
    assert detail["extraction"]["validation_errors"]
