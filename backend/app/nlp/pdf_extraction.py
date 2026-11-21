"""Stage 1: PDF text extraction (PyMuPDF), with page numbers and metadata.

Scanned pages (no text layer) are detected and reported as warnings. OCR is NOT
enabled in this project: a PDF with no extractable text at all is rejected with
a clear error instead of silently producing an empty paper.
"""
import os
from dataclasses import dataclass, field

MIN_CHARS_PER_PAGE = 20


class ExtractionError(Exception):
    """Raised when a PDF cannot be turned into usable text."""


@dataclass
class ExtractionResult:
    pages: list = field(default_factory=list)     # [(page_number_1_based, raw_text)]
    metadata: dict = field(default_factory=dict)  # title, authors, num_pages
    warnings: list = field(default_factory=list)
    method: str = ""


def _guess_title_pymupdf(doc):
    """Title heuristic: the text with the largest font size on page 1."""
    try:
        page = doc[0]
        best_size, best_text = 0.0, ""
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                text = " ".join(s.get("text", "") for s in line.get("spans", [])).strip()
                if not text:
                    continue
                size = max((s.get("size", 0) for s in line.get("spans", [])), default=0)
                if size > best_size:
                    best_size, best_text = size, text
        return best_text[:300] or None
    except Exception:
        return None


def _extract_pymupdf(path, fitz):
    result = ExtractionResult(method="pymupdf")
    doc = fitz.open(path)
    try:
        if getattr(doc, "needs_pass", False):
            raise ExtractionError("The PDF is password protected.")
        meta = doc.metadata or {}
        title = (meta.get("title") or "").strip() or _guess_title_pymupdf(doc)
        result.metadata = {
            "title": title,
            "authors": (meta.get("author") or "").strip() or None,
            "num_pages": doc.page_count,
        }
        for i in range(doc.page_count):
            text = doc[i].get_text("text") or ""
            result.pages.append((i + 1, text))
    finally:
        doc.close()
    return result


def _extract_pypdf(path, pypdf):
    result = ExtractionResult(method="pypdf")
    reader = pypdf.PdfReader(path)
    if getattr(reader, "is_encrypted", False):
        raise ExtractionError("The PDF is password protected.")
    meta = reader.metadata or {}
    result.metadata = {
        "title": (getattr(meta, "title", None) or "").strip() or None,
        "authors": (getattr(meta, "author", None) or "").strip() or None,
        "num_pages": len(reader.pages),
    }
    for i, page in enumerate(reader.pages):
        result.pages.append((i + 1, page.extract_text() or ""))
    return result


def extract_pdf(path):
    """Extract per-page text. PyMuPDF is the primary extractor; pypdf is used
    only if PyMuPDF is not installed."""
    if not os.path.exists(path):
        raise ExtractionError("PDF file not found on disk.")

    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None

    try:
        if fitz is not None:
            result = _extract_pymupdf(path, fitz)
        else:
            try:
                import pypdf
            except ImportError:
                raise ExtractionError(
                    "PyMuPDF is not installed. Run: pip install pymupdf")
            result = _extract_pypdf(path, pypdf)
    except ExtractionError:
        raise
    except Exception as exc:  # corrupt / unsupported PDF
        raise ExtractionError(f"Could not read the PDF: {exc}")

    empty_pages = [n for n, t in result.pages if len(t.strip()) < MIN_CHARS_PER_PAGE]
    if len(empty_pages) == len(result.pages):
        raise ExtractionError(
            "No extractable text found. The PDF may be scanned images; OCR is "
            "not enabled in this project.")
    if empty_pages:
        shown = ", ".join(str(n) for n in empty_pages[:10])
        result.warnings.append(
            f"{len(empty_pages)} page(s) have no text layer (possibly scanned or "
            f"figure-only): {shown}. They were skipped.")
    return result
