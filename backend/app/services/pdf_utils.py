# pdf_utils.py — PDF helpers for student answer-sheet processing.
# Uses PyMuPDF (fitz) — pure-Python, no system dependencies required.

from __future__ import annotations

try:
    import fitz          # PyMuPDF
    _FITZ = True
except ImportError:
    _FITZ = False


def pdf_to_image(pdf_path: str, page_index: int = 0, dpi: int = 200) -> str:
    """
    Render one page of a PDF to a PNG file.
    Returns the path of the saved PNG (same directory as the PDF).
    Used before OMR/TrOCR when the student uploads a PDF answer sheet.
    """
    if not _FITZ:
        raise RuntimeError("PyMuPDF (fitz) not installed. Run: pip install pymupdf")

    doc = fitz.open(pdf_path)
    if page_index >= len(doc):
        page_index = 0
    page = doc[page_index]

    # Scale to requested DPI (PDF default is 72 DPI)
    scale = dpi / 72
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    img_path = pdf_path.rsplit(".", 1)[0] + f"_p{page_index}.png"
    pix.save(img_path)
    doc.close()
    return img_path


def pdf_extract_text(pdf_path: str) -> str:
    """
    Extract selectable text from every page of a PDF.
    Returns empty string for scanned/image-only PDFs.
    Used for handwritten PDFs that are actually typed — skips TrOCR entirely.
    """
    if not _FITZ:
        return ""

    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc).strip()
    doc.close()
    return text


def is_pdf(file_path: str) -> bool:
    return file_path.lower().endswith(".pdf")
