"""Retrieval evaluation on labelled queries supplied by the user.

Nothing is pre-computed or stored: the metrics are calculated from the request
body each time. A handful of queries is a smoke test, not a benchmark."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from app.nlp import vector_store
from app.nlp.embeddings import get_embedder
from app.nlp.metrics import evaluate_retrieval
from app.routes._helpers import owned_project, bad_request

evaluation_bp = Blueprint("evaluation", __name__, url_prefix="/api/projects")


@evaluation_bp.route("/<int:project_id>/evaluation/retrieval", methods=["POST"])
@jwt_required()
def retrieval_eval(project_id):
    """Body: {"k": 5, "queries": [{"question": "...", "relevant_chunk_ids": [1,2]}  # or relevant_paper_ids
    ]}"""
    project, err = owned_project(project_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    queries = data.get("queries") or []
    k = int(data.get("k") or 5)
    if not queries:
        return bad_request("queries is required")
    embedder = get_embedder()

    prepared = []
    for q in queries:
        text = (q.get("question") or "").strip()
        use_papers = "relevant_paper_ids" in q
        relevant = q.get("relevant_paper_ids") if use_papers else q.get("relevant_chunk_ids")
        if not text or relevant is None:
            return bad_request("each query needs question and relevant_chunk_ids or relevant_paper_ids")
        qv = embedder.encode([text])[0]
        hits, _ = vector_store.search(project.id, qv, embedder.name, max(k, 50))
        ranked = [(c.paper_id if use_papers else c.id) for c, _ in hits]
        if use_papers:                                   # keep first occurrence of each paper
            seen = []
            for pid in ranked:
                if pid not in seen:
                    seen.append(pid)
            ranked = seen
        prepared.append({"ranked_ids": ranked, "relevant_ids": relevant})

    metrics = evaluate_retrieval(prepared, k)
    metrics["embedding_backend"] = embedder.name
    metrics["evaluation_type"] = ("smoke test" if len(prepared) < 30 else "user-supplied labelled set")
    metrics["note"] = ("Metrics are computed only from the labelled queries in this request. "
                       "A small hand-made set is a smoke test, not a benchmark.")
    return jsonify(metrics), 200
