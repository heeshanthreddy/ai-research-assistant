from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.chunk import Chunk
from app.routes._helpers import owned_project, bad_request
from app.services.paper_service import (
    create_paper, get_project_papers, get_paper_by_id, delete_paper, paper_to_dict
)
from app.services.processing_service import process_paper, reindex_project
from app.utils.file_storage import save_paper_file, is_pdf

papers_bp = Blueprint(
    "papers",
    __name__,
    url_prefix="/api/projects"
)


def chunk_to_dict(c, with_text=True):
    d = {
        "id": c.id, "paper_id": c.paper_id, "chunk_index": c.chunk_index,
        "page_start": c.page_start, "page_end": c.page_end, "word_count": c.word_count,
        "embedding_backend": c.embedding_backend,
    }
    if with_text:
        d["text"] = c.text
    return d


@papers_bp.route("/<int:project_id>/papers", methods=["POST"])
@jwt_required()
def upload_paper(project_id):

    project, err = owned_project(project_id)
    if err:
        return err

    file = request.files.get("file")

    if file is None or not file.filename:
        return bad_request("No file provided")

    if not file.filename.lower().endswith(".pdf") or not is_pdf(file):
        return bad_request("Only PDF files are accepted (the file is not a valid PDF)", 415)

    original_filename, file_path = save_paper_file(file)
    with open(file_path, "rb") as fh:
        size = len(fh.read())

    paper = create_paper(project_id=project.id, original_filename=original_filename,
                         file_path=file_path, file_size=size)
    paper = process_paper(paper)          # synchronous; failures are stored on the paper

    return jsonify({
        "message": "Paper uploaded and processed" if paper.status == "PROCESSED"
                   else "Paper uploaded but processing failed",
        "paper": paper_to_dict(paper)
    }), 201


@papers_bp.route("/<int:project_id>/papers", methods=["GET"])
@jwt_required()
def list_papers(project_id):
    project, err = owned_project(project_id)
    if err:
        return err
    return jsonify({"papers": [paper_to_dict(p) for p in get_project_papers(project.id)]}), 200


@papers_bp.route("/<int:project_id>/papers/<int:paper_id>", methods=["GET"])
@jwt_required()
def get_paper(project_id, paper_id):
    project, err = owned_project(project_id)
    if err:
        return err
    paper = get_paper_by_id(paper_id, project.id)
    if paper is None:
        return bad_request("Paper not found", 404)
    return jsonify({"paper": paper_to_dict(paper)}), 200


@papers_bp.route("/<int:project_id>/papers/<int:paper_id>", methods=["DELETE"])
@jwt_required()
def remove_paper(project_id, paper_id):
    project, err = owned_project(project_id)
    if err:
        return err
    paper = get_paper_by_id(paper_id, project.id)
    if paper is None:
        return bad_request("Paper not found", 404)
    delete_paper(paper)
    return jsonify({"message": "Paper deleted"}), 200


@papers_bp.route("/<int:project_id>/papers/<int:paper_id>/chunks", methods=["GET"])
@jwt_required()
def paper_chunks(project_id, paper_id):
    project, err = owned_project(project_id)
    if err:
        return err
    paper = get_paper_by_id(paper_id, project.id)
    if paper is None:
        return bad_request("Paper not found", 404)
    chunks = paper.chunks.order_by(Chunk.chunk_index).all()
    return jsonify({"paper": paper_to_dict(paper, with_chunk_count=False),
                    "chunks": [chunk_to_dict(c) for c in chunks]}), 200


@papers_bp.route("/<int:project_id>/chunks/<int:chunk_id>", methods=["GET"])
@jwt_required()
def get_chunk(project_id, chunk_id):
    """Open the passage behind a citation."""
    project, err = owned_project(project_id)
    if err:
        return err
    chunk = Chunk.query.filter_by(id=chunk_id, project_id=project.id).first()
    if chunk is None:
        return bad_request("Chunk not found", 404)
    paper = get_paper_by_id(chunk.paper_id, project.id)
    d = chunk_to_dict(chunk)
    d["paper_title"] = (paper.title or paper.original_filename) if paper else None
    return jsonify({"chunk": d}), 200


@papers_bp.route("/<int:project_id>/reindex", methods=["POST"])
@jwt_required()
def reindex(project_id):
    project, err = owned_project(project_id)
    if err:
        return err
    n = reindex_project(project.id)
    return jsonify({"message": f"Re-embedded {n} chunk(s) with the current embedder", "chunks": n}), 200
