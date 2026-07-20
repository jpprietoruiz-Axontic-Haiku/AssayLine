import fitz


def make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=11)
    return doc.tobytes()


def make_blank_png_bytes() -> bytes:
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 20))
    pixmap.set_rect(pixmap.irect, (255, 255, 255))
    return pixmap.tobytes("png")


SYNTHETIC_CERTIFICATE_TEXT = """CERTIFICADO DE ANALISIS
Producto: Reactivo XYZ
Lote: ABC123
Fecha: 2026-01-15
pH: 7.2
Pureza: 99.5 %
"""
