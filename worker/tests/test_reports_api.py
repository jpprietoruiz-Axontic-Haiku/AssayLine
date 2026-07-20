from app.services import vision
from tests.fixtures import SYNTHETIC_CERTIFICATE_TEXT, make_blank_png_bytes, make_pdf_bytes


def test_upload_pdf_with_embedded_text_is_classified_without_vision_call(
    client, monkeypatch
) -> None:
    calls = []
    monkeypatch.setattr(vision, "transcribe_page", lambda *a, **k: calls.append(1) or "unused")

    pdf_bytes = make_pdf_bytes(SYNTHETIC_CERTIFICATE_TEXT)
    response = client.post(
        "/reports", files={"file": ("certificate.pdf", pdf_bytes, "application/pdf")}
    )

    assert response.status_code == 201
    report_id = response.json()["id"]

    detail = client.get(f"/reports/{report_id}").json()
    assert detail["status"] == "transcribed"
    assert detail["report_type"] == "certificate_of_analysis"
    assert detail["error_message"] is None
    assert calls == []  # embedded text was long enough; vision fallback not needed


def test_upload_image_falls_back_to_vision_transcription(client, monkeypatch) -> None:
    monkeypatch.setattr(
        vision, "transcribe_page", lambda image_bytes, image_ext: "REGISTRO DE PROCESO: OK"
    )

    png_bytes = make_blank_png_bytes()
    response = client.post("/reports", files={"file": ("scan.png", png_bytes, "image/png")})

    assert response.status_code == 201
    report_id = response.json()["id"]

    detail = client.get(f"/reports/{report_id}").json()
    assert detail["status"] == "transcribed"
    assert detail["report_type"] == "process_log"


def test_rejects_unsupported_file_type(client) -> None:
    response = client.post(
        "/reports", files={"file": ("notes.txt", b"plain text", "text/plain")}
    )

    assert response.status_code == 415


def test_get_report_404_when_missing(client) -> None:
    response = client.get("/reports/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
