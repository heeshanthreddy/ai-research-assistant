"""Stage 2: text cleaning and sentence segmentation.

Sentence splitting is rule-based. Periods inside decimals, common academic
abbreviations ("et al.", "Fig.", "e.g."), author initials and dotted acronyms are
protected before splitting so they do not end a sentence.
"""
import re
from collections import Counter
from dataclasses import dataclass

_LIGATURES = {"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl",
              "\u00ad": "", "\u00a0": " ", "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'}

_PH = "\u0001"   # placeholder for a protected period

_ABBREVIATIONS = [
    "et al", "fig", "figs", "eq", "eqs", "sec", "secs", "tab", "ref", "refs", "vs", "cf",
    "approx", "dr", "prof", "mr", "mrs", "ms", "resp", "viz", "inc", "ltd",
]
_ABBR_RE = re.compile(r"\b(" + "|".join(re.escape(a) for a in _ABBREVIATIONS) + r")\.", re.IGNORECASE)
_NUM_ABBR_RE = re.compile(r"\b(No|Nos|pp?|Vol|Ch)\.(?=\s*\d)")   # "No. 5", "pp. 3-9"
_DECIMAL_RE = re.compile(r"(\d)\.(\d)")
_DOTTED_RE = re.compile(r"\b(?:[A-Za-z]\.){2,}")          # e.g. i.e. U.S. Ph.D.
_INITIAL_RE = re.compile(r"\b([A-Z])\.(?=\s+[A-Z])")      # K. Reddy
_SPLIT_RE = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(\[])")


def _normalise_chars(text):
    for a, b in _LIGATURES.items():
        text = text.replace(a, b)
    return text


def clean_page_text(text):
    """Clean one page: ligatures, hyphenation, line joining, page numbers."""
    text = _normalise_chars(text or "")
    text = text.replace("\r", "\n")
    # join words hyphenated across a line break: "seman-\ntic" -> "semantic"
    text = re.sub(r"(\w)-\n\s*([a-z])", r"\1\2", text)

    lines = [ln.strip() for ln in text.split("\n")]
    # drop stand-alone page numbers and "Page 3 of 10"
    lines = [ln for ln in lines
             if not re.fullmatch(r"\d{1,4}", ln)
             and not re.fullmatch(r"(?i)page\s+\d+(\s+of\s+\d+)?", ln)]

    out = []
    for i, ln in enumerate(lines):
        if not ln:
            if out and out[-1] != "\n":
                out.append("\n")
            continue
        out.append(ln)
        nxt = next((l for l in lines[i + 1:] if l), "")
        heading_like = (len(ln) <= 60 and not re.search(r"[.,;:]$", ln)
                        and re.match(r"[A-Z0-9]", ln) and (nxt[:1].isupper() or nxt[:1].isdigit()))
        out.append("\n" if heading_like else " ")
    joined = "".join(out)
    joined = re.sub(r"[ \t]+", " ", joined)
    joined = re.sub(r" ?\n ?", "\n", joined)
    return re.sub(r"\n{2,}", "\n", joined).strip()


def remove_repeated_lines(pages):
    """Drop running headers/footers: short RAW lines present on >= half of the pages.

    Must run on raw lines, before clean_page_text() joins lines together
    (otherwise a header gets merged into the following text line)."""
    if len(pages) < 3:
        return pages
    counts = Counter()
    for _, text in pages:
        for ln in {l.strip() for l in text.split("\n") if l.strip()}:
            if len(ln) < 80:
                counts[ln] += 1
    repeated = {ln for ln, c in counts.items() if c >= max(3, len(pages) / 2)}
    return [(n, "\n".join(l for l in text.split("\n") if l.strip() not in repeated))
            for n, text in pages]


def split_sentences(text):
    """Rule-based sentence segmentation with abbreviation/decimal protection."""
    if not text or not text.strip():
        return []
    protected = _DOTTED_RE.sub(lambda m: m.group(0).replace(".", _PH), text)
    protected = _ABBR_RE.sub(lambda m: m.group(1) + _PH, protected)
    protected = _NUM_ABBR_RE.sub(lambda m: m.group(1) + _PH, protected)
    protected = _DECIMAL_RE.sub(lambda m: m.group(1) + _PH + m.group(2), protected)
    protected = _INITIAL_RE.sub(lambda m: m.group(1) + _PH, protected)

    sentences = []
    for block in protected.split("\n"):          # newline = heading/paragraph boundary
        for s in _SPLIT_RE.split(block):
            s = s.replace(_PH, ".").strip()
            if s:
                sentences.append(re.sub(r"\s+", " ", s))
    # glue tiny fragments (e.g. a stray "1." or ")") to the previous sentence
    merged = []
    for s in sentences:
        if merged and len(s) < 3:
            merged[-1] = merged[-1] + " " + s
        else:
            merged.append(s)
    return merged


@dataclass
class Sentence:
    text: str
    page: int


def segment_document(pages):
    """pages: [(page_no, raw_text)] -> [Sentence] with source page numbers."""
    pages = remove_repeated_lines([(n, _normalise_chars(t or "")) for n, t in pages])
    cleaned = [(n, clean_page_text(t)) for n, t in pages]
    out = []
    for n, text in cleaned:
        for s in split_sentences(text):
            # a sentence continued across a page break: join it to the previous one
            if (out and out[-1].page == n - 1 and not re.search(r"[.!?][\"')\]]*$", out[-1].text)
                    and s[:1].islower()):
                out[-1].text += " " + s
            else:
                out.append(Sentence(s, n))
    return out
