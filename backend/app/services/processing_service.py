"""Runs the local pipeline for one uploaded paper:
PDF -> text (PyMuPDF) -> cleaning/segmentation -> semantic chunks -> embeddings -> SQL store.
"""
import logging
import os
from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models.chunk import Chunk
from app.nlp import vector_store
from app.nlp.chunking import semantic_chunk
from app.nlp.embeddings import get_embedder
from app.nlp.pdf_extraction import extract_pdf, ExtractionError
from app.nlp.preprocessing import segment_document

log = logging.getLogger(__name__)


def process_paper(paper):
    """Process a stored paper synchronously. Never raises: failures are recorded
    on the paper (status FAILED + processing_error)."""
    cfg = current_app.config
    paper.status = "PROCESSING"
    paper.processing_error = None
    db.session.commit()
    try:
        extraction = extract_pdf(paper.file_path)
        paper.extraction_method = extraction.method
        paper.num_pages = extraction.metadata.get("num_pages")
        if not paper.title:
            paper.title = (extraction.metadata.get("title")
                           or os.path.splitext(paper.original_filename)[0])
        if not paper.authors:
            paper.authors = extraction.metadata.get("authors")

        sentences = segment_document(extraction.pages)
        if not sentences:
            raise ExtractionError("No sentences could be extracted from the text.")

        embedder = get_embedder()
        chunks = semantic_chunk(sentences, embedder.encode,
                                min_tokens=cfg["CHUNK_MIN_TOKENS"], max_tokens=cfg["CHUNK_MAX_TOKENS"],
                                break_std=cfg["CHUNK_BREAK_STD"], window=cfg["CHUNK_WINDOW"])
        vectors = embedder.encode([c["text"] for c in chunks])

        Chunk.query.filter_by(paper_id=paper.id).delete()
        vector_store.save_chunks(paper, chunks, vectors, embedder.name)

        paper.processing_warnings = "\n".join(extraction.warnings) or None
        paper.status = "PROCESSED"
        paper.processed_at = datetime.utcnow()
    except ExtractionError as exc:
        db.session.rollback()
        paper.status, paper.processing_error = "FAILED", str(exc)
    except Exception as exc:                       # keep the app usable on any failure
        db.session.rollback()
        log.exception("Processing failed for paper %s", paper.id)
        paper.status, paper.processing_error = "FAILED", f"Unexpected error: {exc}"
    db.session.commit()
    return paper


def reindex_project(project_id):
    """Re-embed every chunk of a project with the CURRENT embedder (e.g. after
    switching from the hashing fallback to MiniLM). Chunk boundaries are kept."""
    embedder = get_embedder()
    chunks = Chunk.query.filter_by(project_id=project_id).all()
    if not chunks:
        return 0
    vectors = embedder.encode([c.text for c in chunks])
    for c, v in zip(chunks, vectors):
        c.embedding = vector_store.to_bytes(v)
        c.embedding_backend = embedder.name
    db.session.commit()
    return len(chunks)
