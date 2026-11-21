"""Research idea analysis (corpus-relative).

* The idea text is embedded with the same local embedder as the papers.
* Each paper is represented by the normalised mean of its chunk embeddings.
* The closest papers (cosine) are returned with their best matching passages.
* S = mean cosine similarity of the closest papers (default 3).
* novelty_estimate = 1 - S, with NO further normalisation and NO verdict
  thresholds. It is an uncalibrated indicator relative to the UPLOADED corpus.
  A high value does not show that an idea is new to the research field.
* Possible gaps: content-word bigrams of the idea that occur in none of the
  uploaded papers' text (a simple lexical check, not proof of a research gap).
"""
import re
from collections import defaultdict

import numpy as np

from app.nlp import vector_store
from app.nlp.stopwords import STOPWORDS



_TOKEN_RE = re.compile(r"[a-z][a-z0-9\-]+")


def content_bigrams(text):
    toks = [t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 2]
    seen, out = set(), []
    for a, b in zip(toks, toks[1:]):
        bg = f"{a} {b}"
        if bg not in seen:
            seen.add(bg)
            out.append(bg)
    return out


def analyse_idea(project_id, idea, embedder, papers_by_id, top_papers=3):
    chunks, matrix, stale = vector_store.load_project_vectors(project_id, embedder.name)
    base = {"idea": idea, "embedding": embedder.info(),
            "scope_note": ("Relative to the uploaded papers only. Lower similarity to this corpus "
                           "suggests a potentially less explored direction but does not prove "
                           "global novelty; expert judgement is required.")}
    if not chunks:
        return {**base, "available": False,
                "reason": "No processed papers for this embedding backend."}

    qv = embedder.encode([idea])[0]
    chunk_sims = matrix @ qv

    by_paper = defaultdict(list)
    for i, c in enumerate(chunks):
        by_paper[c.paper_id].append(i)

    paper_rows = []
    for pid, idxs in by_paper.items():
        centroid = matrix[idxs].mean(axis=0)
        norm = np.linalg.norm(centroid)
        centroid = centroid / norm if norm > 0 else centroid
        best_i = max(idxs, key=lambda i: chunk_sims[i])
        paper = papers_by_id.get(pid)
        paper_rows.append({
            "paper_id": pid,
            "paper_title": (paper.title or paper.original_filename) if paper else str(pid),
            "similarity": float(centroid @ qv),
            "best_passage": {"chunk_id": chunks[best_i].id, "page_start": chunks[best_i].page_start,
                             "page_end": chunks[best_i].page_end, "text": chunks[best_i].text,
                             "similarity": float(chunk_sims[best_i])},
        })
    paper_rows.sort(key=lambda r: -r["similarity"])
    closest = paper_rows[:top_papers]
    s_avg = float(np.mean([r["similarity"] for r in closest]))

    corpus_text = " ".join(c.text.lower() for c in chunks)
    corpus_text = re.sub(r"[^a-z0-9\-]+", " ", corpus_text)
    gaps = [bg for bg in content_bigrams(idea) if f" {bg} " not in f" {corpus_text} "]

    return {**base, "available": True,
            "papers_in_corpus": len(paper_rows),
            "closest_papers": closest,
            "average_similarity_closest": round(s_avg, 4),
            "novelty_estimate": round(1.0 - s_avg, 4),
            "novelty_note": ("novelty_estimate = 1 - average similarity of the closest papers. "
                             "Uncalibrated: no normalisation and no verdict thresholds are applied."),
            "possible_gaps": gaps,
            "gaps_note": "Idea bigrams absent from the uploaded text: possible gaps in THIS corpus only."}
