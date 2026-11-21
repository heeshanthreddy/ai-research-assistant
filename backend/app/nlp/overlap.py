"""Semantic overlap detection against the user's OWN uploaded corpus.

Not a web-scale plagiarism detector. Two stages:
  1. vector search retrieves the top chunks that could contain a match;
  2. each input sentence is compared with every individual sentence in those
     chunks (a copied sentence scores poorly against a whole 200-word chunk).
A match is reported when cosine similarity >= the backend-specific threshold.
"""
from app.nlp.preprocessing import split_sentences
from app.nlp import vector_store


def check_overlap(project_id, text, embedder, cfg, papers_by_id):
    threshold = (cfg["OVERLAP_THRESHOLD_SEMANTIC"] if embedder.is_semantic
                 else cfg["OVERLAP_THRESHOLD_LEXICAL"])
    top_chunks = cfg["OVERLAP_TOP_CHUNKS"]
    sentences = split_sentences(text)
    out = {"threshold": threshold, "embedding": embedder.info(),
           "scope_note": ("Overlap checker against the user's uploaded papers only. "
                          "It is not a web-scale plagiarism detector."),
           "sentences": []}
    if not sentences:
        return {**out, "flagged": 0, "message": "No sentences found in the input."}

    qvecs = embedder.encode(sentences)
    chunk_sent_cache = {}
    flagged = 0
    for sent, qv in zip(sentences, qvecs):
        hits, _ = vector_store.search(project_id, qv, embedder.name, top_chunks)
        best = None
        for chunk, chunk_score in hits:
            if chunk.id not in chunk_sent_cache:
                ss = split_sentences(chunk.text) or [chunk.text]
                chunk_sent_cache[chunk.id] = (ss, embedder.encode(ss))
            ss, mat = chunk_sent_cache[chunk.id]
            sims = mat @ qv
            j = int(sims.argmax())
            if best is None or float(sims[j]) > best["similarity"]:
                paper = papers_by_id.get(chunk.paper_id)
                best = {"similarity": float(sims[j]), "matched_sentence": ss[j],
                        "chunk_id": chunk.id, "paper_id": chunk.paper_id,
                        "paper_title": (paper.title or paper.original_filename) if paper else None,
                        "page_start": chunk.page_start, "page_end": chunk.page_end,
                        "passage": chunk.text}
        is_flag = best is not None and best["similarity"] >= threshold
        flagged += int(is_flag)
        if best:
            best["similarity"] = round(best["similarity"], 4)
        out["sentences"].append({"sentence": sent, "flagged": is_flag, "match": best})
    out["flagged"] = flagged
    out["total_sentences"] = len(sentences)
    return out
