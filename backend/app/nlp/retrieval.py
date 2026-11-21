"""Stage 5-6: retrieval + Maximal Marginal Relevance (MMR) re-ranking.

All scores are COSINE SIMILARITIES (higher = closer). Nothing here uses
distances, so there is no 1 - d conversion to get wrong.

    MMR(d) = lambda * sim(q, d) - (1 - lambda) * max_{s in selected} sim(d, s)
"""
import numpy as np

from app.nlp import vector_store
from app.nlp.vector_store import from_bytes


def mmr(query_vec, cand_vecs, k, lam):
    """Return indices (into cand_vecs) chosen by MMR, in selection order."""
    cand_vecs = np.asarray(cand_vecs, dtype=np.float32)
    n = len(cand_vecs)
    if n == 0:
        return []
    rel = cand_vecs @ np.asarray(query_vec, dtype=np.float32)
    pair = cand_vecs @ cand_vecs.T
    selected, remaining = [], list(range(n))
    while remaining and len(selected) < k:
        if not selected:
            best = max(remaining, key=lambda i: rel[i])
        else:
            best = max(remaining,
                       key=lambda i: lam * rel[i] - (1 - lam) * max(pair[i][j] for j in selected))
        selected.append(best)
        remaining.remove(best)
    return selected


def retrieve(project_id, question, embedder, candidates=18, top_k=6, lam=0.7):
    """Embed the question, fetch `candidates` nearest chunks, MMR-select `top_k`.

    Returns (results, info) where results = [{"chunk", "score"}] (score is the
    cosine similarity between question and chunk) in MMR order.
    """
    qv = embedder.encode([question])[0]
    hits, stale = vector_store.search(project_id, qv, embedder.name, candidates)
    info = {"candidates": len(hits), "stale_chunks": stale}
    if not hits:
        return [], info
    cand_vecs = np.vstack([from_bytes(c.embedding) for c, _ in hits])
    order = mmr(qv, cand_vecs, top_k, lam)
    return [{"chunk": hits[i][0], "score": hits[i][1]} for i in order], info
