"""PDF extraction tests.

* Logic tests use a stand-in `fitz` module so the PyMuPDF branch is exercised
  even where PyMuPDF is not installed. They check OUR code's use of the PyMuPDF
  interface (open/page_count/get_text/metadata), not PyMuPDF itself.
* The real-PDF test runs through whichever extractor is installed (PyMuPDF if
  present, otherwise pypdf) and reports which one was used.
"""
import os
import sys
import tempfile
import types
import unittest

from app.nlp import pdf_extraction as px
from tests.make_test_pdf import build


class _FakePage:
    def __init__(self, text): self._t = text
    def get_text(self, mode="text"):
        if mode == "dict":
            return {"blocks": [{"lines": [{"spans": [{"text": "Big Title", "size": 20}]},
                                          {"spans": [{"text": "small", "size": 9}]}]}]}
        return self._t


class _FakeDoc:
    def __init__(self, pages, meta, needs_pass=False):
        self._p = [_FakePage(t) for t in pages]
        self.metadata, self.needs_pass = meta, needs_pass
        self.page_count = len(pages)
    def __getitem__(self, i): return self._p[i]
    def close(self): pass


def _install_fake_fitz(pages, meta, needs_pass=False):
    mod = types.ModuleType("fitz")
    mod.open = lambda path: _FakeDoc(pages, meta, needs_pass)
    sys.modules["fitz"] = mod


class FakeFitzLogic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.tmp.write(b"%PDF-1.4"); self.tmp.close()
        self._old = sys.modules.get("fitz")

    def tearDown(self):
        os.unlink(self.tmp.name)
        if self._old is None: sys.modules.pop("fitz", None)
        else: sys.modules["fitz"] = self._old

    def test_pages_metadata_and_scanned_page_warning(self):
        _install_fake_fitz(["Some real text on page one here.", "  ", "More real text on page three."],
                           {"title": "", "author": "A. Author"})
        r = px.extract_pdf(self.tmp.name)
        self.assertEqual(r.method, "pymupdf")
        self.assertEqual([n for n, _ in r.pages], [1, 2, 3])
        self.assertEqual(r.metadata["title"], "Big Title")           # largest-font fallback
        self.assertEqual(r.metadata["authors"], "A. Author")
        self.assertEqual(r.metadata["num_pages"], 3)
        self.assertTrue(any("1 page(s) have no text layer" in w for w in r.warnings))

    def test_fully_scanned_pdf_is_rejected_with_clear_message(self):
        _install_fake_fitz(["", " "], {})
        with self.assertRaises(px.ExtractionError) as cm:
            px.extract_pdf(self.tmp.name)
        self.assertIn("OCR", str(cm.exception))

    def test_password_protected(self):
        _install_fake_fitz(["text"], {}, needs_pass=True)
        with self.assertRaises(px.ExtractionError):
            px.extract_pdf(self.tmp.name)

    def test_missing_file(self):
        with self.assertRaises(px.ExtractionError):
            px.extract_pdf("/no/such/file.pdf")


class RealPdf(unittest.TestCase):
    def test_extracts_text_pages_and_title(self):
        try:
            import reportlab  # noqa: F401
        except ImportError:
            self.skipTest("reportlab not installed (pip install reportlab) - used only to build a test PDF")
        sys.modules.pop("fitz", None)
        with tempfile.TemporaryDirectory() as d:
            path = build(os.path.join(d, "t.pdf"))
            r = px.extract_pdf(path)
        print(f"\n   [real-PDF test used extractor: {r.method}]")
        self.assertEqual(len(r.pages), 3)
        self.assertIn("Dense retrieval", r.pages[0][1])
        self.assertEqual(r.metadata["num_pages"], 3)

    def test_corrupt_pdf_raises_extraction_error(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 this is not really a pdf")
        try:
            sys.modules.pop("fitz", None)
            with self.assertRaises(px.ExtractionError):
                px.extract_pdf(f.name)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
