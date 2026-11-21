from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.services.project_service import get_project_by_id


def current_user_id():
    return int(get_jwt_identity())


def owned_project(project_id):
    """Return (project, None) for the logged-in owner, or (None, error_response)."""
    project = get_project_by_id(project_id, current_user_id())
    if project is None:
        return None, (jsonify({"error": "Project not found", "message": "Project not found"}), 404)
    return project, None


def bad_request(msg, status=400):
    return jsonify({"error": msg, "message": msg}), status


def papers_by_id(project):
    return {p.id: p for p in project.papers}
