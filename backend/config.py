import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _int(name, default):
    return int(os.getenv(name, default))


def _float(name, default):
    return float(os.getenv(name, default))


class Config:
    # --- original settings (unchanged names) ---------------------------------
    # Defaults are only a convenience for local demos; set real values in .env.
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-change-me"

    # PostgreSQL (as originally configured) works unchanged. If DATABASE_URL is
    # not set we fall back to a local SQLite file so the app still starts.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or "sqlite:///researchforge.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or "dev-jwt-secret-change-me-0123456789abcdef"

    # --- uploads --------------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "papers")
    MAX_CONTENT_LENGTH = _int("MAX_UPLOAD_MB", 25) * 1024 * 1024

    # --- local NLP pipeline (no external API keys anywhere) -------------------
    # auto   : sentence-transformers MiniLM if it can be loaded, else hashing
    # minilm : MiniLM only (error if unavailable)
    # hashing: lexical hashing embedder only (NOT semantic)
    EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto").lower()
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    HASHING_DIM = _int("HASHING_DIM", 1024)

    # Chunking. Words are used as a cheap token count. These defaults come from
    # the project's design notes; they are NOT tuned on a benchmark.
    CHUNK_MIN_TOKENS = _int("CHUNK_MIN_TOKENS", 40)
    CHUNK_MAX_TOKENS = _int("CHUNK_MAX_TOKENS", 220)
    CHUNK_BREAK_STD = _float("CHUNK_BREAK_STD", 0.5)   # cut where sim < mean - k*std
    CHUNK_WINDOW = _int("CHUNK_WINDOW", 3)             # sentences on each side of a gap

    # Retrieval + MMR (all cosine similarities, higher = more similar).
    RETRIEVAL_CANDIDATES = _int("RETRIEVAL_CANDIDATES", 18)
    RETRIEVAL_TOP_K = _int("RETRIEVAL_TOP_K", 6)
    MMR_LAMBDA = _float("MMR_LAMBDA", 0.7)

    # Extractive QA.
    QA_MAX_SENTENCES = _int("QA_MAX_SENTENCES", 3)
    QA_RELATIVE_CUTOFF = _float("QA_RELATIVE_CUTOFF", 0.5)  # keep >= 50% of best score
    # Absolute floors below which we answer "insufficient evidence". Separate
    # values because lexical (hashing) and semantic (MiniLM) cosines have very
    # different ranges. Engineering defaults, untuned: adjust in .env.
    QA_MIN_SCORE_SEMANTIC = _float("QA_MIN_SCORE_SEMANTIC", 0.25)
    QA_MIN_SCORE_LEXICAL = _float("QA_MIN_SCORE_LEXICAL", 0.10)

    # Citation verification: answer sentence vs best sentence of the cited
    # passage. Engineering defaults, untuned: cosine is a proxy for support.
    CITATION_THRESHOLD_SEMANTIC = _float("CITATION_THRESHOLD_SEMANTIC", 0.60)
    CITATION_THRESHOLD_LEXICAL = _float("CITATION_THRESHOLD_LEXICAL", 0.50)

    # Semantic overlap detection.
    OVERLAP_THRESHOLD_SEMANTIC = _float("OVERLAP_THRESHOLD_SEMANTIC", 0.85)
    OVERLAP_THRESHOLD_LEXICAL = _float("OVERLAP_THRESHOLD_LEXICAL", 0.60)
    OVERLAP_TOP_CHUNKS = _int("OVERLAP_TOP_CHUNKS", 3)

    # Idea analysis.
    IDEA_TOP_PAPERS = _int("IDEA_TOP_PAPERS", 3)
