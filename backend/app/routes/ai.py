"""Local NLP endpoints: extractive QA, citation verification, idea analysis,
overlap detection and the passage-pair classifier. No external APIs are called."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from app.nlp.embeddings import get_embedder, embedder_status
from app.nlp.qa import answer_question
from app.nlp.citations import verify_answer
from app.nlp.idea_analysis import analyse_idea
from app.nlp.overlap import check_overlap
from app.nlp import classifier
from app.routes._helpers import owned_project, bad_request, papers_by_id

ai_bp = Blueprint("ai", __name__, url_prefix="/api")


def _embedder_or_error():
    try:
        return get_embedder(), None
    except Exception as exc:
        return None, bad_request(f"Embedding backend error: {exc}", 503)


def _citation_threshold(embedder):
    cfg = current_app.config
    return (cfg["CITATION_THRESHOLD_SEMANTIC"] if embedder.is_semantic
            else cfg["CITATION_THRESHOLD_LEXICAL"])


@ai_bp.route("/nlp/status", methods=["GET"])
@jwt_required()
def nlp_status():
    try:
        emb = embedder_status()
    except Exception as exc:
        return bad_request(f"Embedding backend error: {exc}", 503)
    cfg = current_app.config
    return jsonify({
        "embedding": emb,
        "qa": {"method": "extractive", "external_api": False},
        "thresholds": {
            "citation": _citation_threshold(get_embedder()),
            "overlap": (cfg["OVERLAP_THRESHOLD_SEMANTIC"] if emb["semantic"]
                        else cfg["OVERLAP_THRESHOLD_LEXICAL"]),
        },
        "pair_classifier": classifier.model_status(),
    }), 200


@ai_bp.route("/projects/<int:project_id>/ask", methods=["POST"])
@jwt_required()
def ask(project_id):
    project, err = owned_project(project_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return bad_request("A question is required")
    embedder, err = _embedder_or_error()
    if err:
        return err

    result = answer_question(project.id, question, embedder, current_app.config, papers_by_id(project))
    if not result["insufficient_evidence"]:
        sources = {s["number"]: s["passage"] for s in result["sources"]}
        result["verification"] = verify_answer(result["answer"], sources, embedder,
                                               _citation_threshold(embedder))
    else:
        result["verification"] = None
    return jsonify(result), 200


@ai_bp.route("/projects/<int:project_id>/verify", methods=["POST"])
@jwt_required()
def verify(project_id):
    """Verify arbitrary text with [n] markers against supplied numbered passages."""
    project, err = owned_project(project_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    answer = (data.get("answer") or "").strip()
    raw_sources = data.get("sources") or []
    if not answer:
        return bad_request("An answer text is required")
    try:
        sources = {int(s["number"]): str(s["passage"]) for s in raw_sources}
    except (KeyError, TypeError, ValueError):
        return bad_request("sources must be a list of {number, passage}")
    embedder, err = _embedder_or_error()
    if err:
        return err
    return jsonify(verify_answer(answer, sources, embedder, _citation_threshold(embedder))), 200


@ai_bp.route("/projects/<int:project_id>/idea", methods=["POST"])
@jwt_required()
def idea(project_id):
    project, err = owned_project(project_id)
    if err:
        return err
    text = ((request.get_json(silent=True) or {}).get("idea") or "").strip()
    if len(text.split()) < 3:
        return bad_request("Describe the idea in at least a few words")
    embedder, err = _embedder_or_error()
    if err:
        return err
    return jsonify(analyse_idea(project.id, text, embedder, papers_by_id(project),
                                current_app.config["IDEA_TOP_PAPERS"])), 200


@ai_bp.route("/projects/<int:project_id>/overlap", methods=["POST"])
@jwt_required()
def overlap(project_id):
    project, err = owned_project(project_id)
    if err:
        return err
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
    if not text:
        return bad_request("Text to check is required")
    embedder, err = _embedder_or_error()
    if err:
        return err
    return jsonify(check_overlap(project.id, text, embedder, current_app.config,
                                 papers_by_id(project))), 200


@ai_bp.route("/nlp/pair-similarity", methods=["POST"])
@jwt_required()
def pair_similarity():
    data = request.get_json(silent=True) or {}
    a, b = (data.get("text_a") or "").strip(), (data.get("text_b") or "").strip()
    if not a or not b:
        return bad_request("text_a and text_b are required")
    embedder, err = _embedder_or_error()
    if err:
        return err
    return jsonify(classifier.classify_pair(a, b, embedder)), 200
