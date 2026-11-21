"""Stage 7: LOCAL EXTRACTIVE question answering.

No generative model and no external API. The answer is built ONLY from sentences
that already exist in the retrieved passages:

  question -> retrieve (+MMR) -> split passages into sentences -> rank sentences by
  cosine similarity to the question -> keep the best few -> add [n] citations.

If the best sentence is below the relevance floor, the system says the evidence is
insufficient instead of guessing.  Retrieval mistakes can still surface a sentence
that is related to, but does not truly answer, the question.
"""
import re
import numpy as np

from app.nlp.preprocessing import split_sentences
from app.nlp.retrieval import retrieve
from app.nlp.citations import compose_with_marker

INSUFFICIENT = ("The uploaded papers do not contain enough evidence to answer this "
                "question.")

_REF_CITE_RE = re.compile(r"\s*\[\d+(?:\s*[,\u2013-]\s*\d+)*\]")   # [12], [3, 4] inside papers


def _source_label(chunk, paper):
    return {
        "chunk_id": chunk.id, "paper_id": chunk.paper_id,
        "paper_title": (paper.title or paper.original_filename) if paper else None,
        "page_start": chunk.page_start, "page_end": chunk.page_end,
        "chunk_index": chunk.chunk_index,
    }


def answer_question(project_id, question, embedder, cfg, papers_by_id):
    min_score = (cfg["QA_MIN_SCORE_SEMANTIC"] if embedder.is_semantic
                 else cfg["QA_MIN_SCORE_LEXICAL"])
    base = {
        "question": question, "method": "extractive",
        "method_note": ("Extractive question answering: every answer sentence is copied from "
                        "the retrieved passages. This is not generative LLM answering."),
        "embedding": embedder.info(), "min_score": min_score,
    }
    results, info = retrieve(project_id, question, embedder, cfg["RETRIEVAL_CANDIDATES"],
                             cfg["RETRIEVAL_TOP_K"], cfg["MMR_LAMBDA"])
    base["retrieval"] = info
    if not results:
        reason = ("No indexed passages for this embedding backend; upload a paper or "
                  "re-index." if info["stale_chunks"] else "No papers have been processed yet.")
        return {**base, "answer": INSUFFICIENT, "insufficient_evidence": True,
                "reason": reason, "sources": []}

    # candidate sentences from the retrieved chunks
    cands = []
    for rank, r in enumerate(results):
        for pos, s in enumerate(split_sentences(r["chunk"].text)):
            if len(s.split()) >= 4:
                cands.append({"i": len(cands), "rank": rank, "pos": pos, "text": s, "chunk": r["chunk"]})
    if not cands:
        return {**base, "answer": INSUFFICIENT, "insufficient_evidence": True,
                "reason": "Retrieved passages contained no usable sentences.", "sources": []}

    vecs = embedder.encode([c["text"] for c in cands] + [question])
    sims = vecs[:-1] @ vecs[-1]
    for c, s in zip(cands, sims):
        c["score"] = float(s)
    ranked = sorted(cands, key=lambda c: -c["score"])
    best = ranked[0]["score"]
    if best < min_score:
        return {**base, "answer": INSUFFICIENT, "insufficient_evidence": True,
                "reason": f"Best sentence similarity {best:.2f} is below the relevance floor {min_score:.2f}.",
                "best_score": best, "sources": []}

    keep = []
    for c in ranked:
        if len(keep) >= cfg["QA_MAX_SENTENCES"]:
            break
        if c["score"] < cfg["QA_RELATIVE_CUTOFF"] * best:
            break
        vec = vecs[c["i"]]
        if any(float(vec @ vecs[k["i"]]) > 0.95 for k in keep):   # near-duplicate
            continue
        keep.append(c)
    keep.sort(key=lambda c: (c["rank"], c["pos"]))      # readable order

    numbering, sources, parts = {}, [], []
    for c in keep:
        cid = c["chunk"].id
        if cid not in numbering:
            numbering[cid] = len(numbering) + 1
            label = _source_label(c["chunk"], papers_by_id.get(c["chunk"].paper_id))
            label.update(number=numbering[cid], passage=c["chunk"].text,
                         relevance=round(next(r["score"] for r in results if r["chunk"].id == cid), 4))
            sources.append(label)
        clean = _REF_CITE_RE.sub("", c["text"]).strip()   # drop the paper's own [12] refs
        parts.append(compose_with_marker(clean, numbering[cid]))

    return {**base, "answer": " ".join(parts), "insufficient_evidence": False,
            "best_score": round(best, 4), "sources": sources,
            "selected_sentences": [{"text": c["text"], "score": round(c["score"], 4),
                                    "source": numbering[c["chunk"].id]} for c in keep]}
