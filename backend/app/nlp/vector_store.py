"""Stage 5: vector storage and similarity search.

Vectors live in the existing SQL database (chunks.embedding, float32 bytes) and
are searched with an exact brute-force cosine scan (numpy dot product on
L2-normalised vectors). Every query is scoped to one project, so the owner
filter in the routes (project must belong to the JWT user) also scopes search.

ChromaDB is NOT used in this implementation. For the corpus sizes this project
targets (hundreds to a few thousand chunks per project) an exact scan is fast,
has no extra dependency, and cannot return approximate results.

Vectors from different embedders are never mixed: search only considers chunks
whose embedding_backend matches the active embedder.
"""
import numpy as np

from app.extensions import db
from app.models.chunk import Chunk


def to_bytes(vec):
    return np.asarray(vec, dtype=np.float32).tobytes()


def from_bytes(blob):
    return np.frombuffer(blob, dtype=np.float32)


def save_chunks(paper, chunk_dicts, vectors, backend_name):
    rows = []
    for c, v in zip(chunk_dicts, vectors):
        rows.append(Chunk(
            paper_id=paper.id, project_id=paper.project_id,
            chunk_index=c["chunk_index"], page_start=c["page_start"], page_end=c["page_end"],
            text=c["text"], word_count=c["word_count"],
            embedding=to_bytes(v), embedding_backend=backend_name))
    db.session.add_all(rows)
    db.session.commit()
    return rows


def load_project_vectors(project_id, backend_name):
    """Return (chunks, matrix, n_stale). n_stale = chunks embedded by another backend."""
    all_chunks = Chunk.query.filter_by(project_id=project_id).order_by(Chunk.paper_id, Chunk.chunk_index).all()
    usable = [c for c in all_chunks if c.embedding and c.embedding_backend == backend_name]
    stale = len(all_chunks) - len(usable)
    if not usable:
        return [], np.zeros((0, 0), dtype=np.float32), stale
    matrix = np.vstack([from_bytes(c.embedding) for c in usable])
    return usable, matrix, stale


def search(project_id, query_vec, backend_name, k):
    """Top-k chunks by cosine similarity. Returns [(Chunk, score)] sorted desc."""
    chunks, matrix, stale = load_project_vectors(project_id, backend_name)
    if not chunks:
        return [], stale
    scores = matrix @ np.asarray(query_vec, dtype=np.float32)
    order = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in order], stale
