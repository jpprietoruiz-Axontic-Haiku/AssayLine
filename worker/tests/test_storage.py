from app.services import storage


def test_save_original_writes_file_with_matching_suffix(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(storage, "_base_dir", lambda: tmp_path)

    path = storage.save_original("report-1", "certificate.pdf", b"%PDF-1.4 fake")

    assert path == tmp_path / "report-1" / "original.pdf"
    assert path.read_bytes() == b"%PDF-1.4 fake"


def test_save_page_image_and_text(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(storage, "_base_dir", lambda: tmp_path)

    image_path = storage.save_page_image("report-1", 0, b"\x89PNG", ext="png")
    text_path = storage.save_page_text("report-1", 0, "hello world")

    assert image_path == tmp_path / "report-1" / "pages" / "page-0.png"
    assert text_path.read_text(encoding="utf-8") == "hello world"
