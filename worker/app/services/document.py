from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

RASTER_DPI = 150
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class PageContent:
    index: int
    image_bytes: bytes
    image_ext: str
    embedded_text: str


def extract_pages(path: Path) -> list[PageContent]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf_pages(path)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return [
            PageContent(
                index=0,
                image_bytes=path.read_bytes(),
                image_ext=suffix.lstrip("."),
                embedded_text="",
            )
        ]
    raise ValueError(f"unsupported file type: {suffix}")


def _extract_pdf_pages(path: Path) -> list[PageContent]:
    pages: list[PageContent] = []
    with fitz.open(path) as doc:
        for index, page in enumerate(doc):
            text = page.get_text().strip()
            pixmap = page.get_pixmap(dpi=RASTER_DPI)
            pages.append(
                PageContent(
                    index=index,
                    image_bytes=pixmap.tobytes("png"),
                    image_ext="png",
                    embedded_text=text,
                )
            )
    return pages
