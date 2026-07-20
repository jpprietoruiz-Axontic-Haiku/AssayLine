from pathlib import Path

from app.core.config import get_settings


def _base_dir() -> Path:
    return Path(get_settings().storage_dir)


def report_dir(report_id: str) -> Path:
    return _base_dir() / report_id


def pages_dir(report_id: str) -> Path:
    return report_dir(report_id) / "pages"


def save_original(report_id: str, filename: str, content: bytes) -> Path:
    suffix = Path(filename).suffix.lower()
    target = report_dir(report_id) / f"original{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


def save_page_image(report_id: str, index: int, image_bytes: bytes, ext: str = "png") -> Path:
    target = pages_dir(report_id) / f"page-{index}.{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)
    return target


def save_page_text(report_id: str, index: int, text: str) -> Path:
    target = pages_dir(report_id) / f"page-{index}.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target
