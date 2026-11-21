from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.project_service import (
    create_project,
    get_user_projects,
    get_project_by_id,
    update_project,
    archive_project,
    delete_project
)


projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


# Method	            Meaning	                                  ResearchForge example
# GET	                Read data	                                Get project
# POST	                Create something	                        Create project
# PUT	                Update/replace resource	                    Update project details
# PATCH	                Partially modify something	                Archive project
# DELETE	            Permanently remove	                        Delete project


@projects_bp.route("/", methods=["POST"])
@jwt_required()
def create_project_route():

    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    research_field = data.get("research_field")

    if not title:
        return jsonify({
            "error": "Title is required"
        }), 400

    user_id = get_jwt_identity()

    project = create_project(
        title=title,
        description=description,
        research_field=research_field,
        user_id=user_id
    )

    return jsonify({
        "message": "Project created successfully",
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "research_field": project.research_field,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    }), 201

@projects_bp.route("/", methods=["GET"])
@jwt_required()
def get_projects():
    user_id = get_jwt_identity()
    projects = get_user_projects(user_id)
    return jsonify({
        "projects": [
            {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "research_field": project.research_field,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
            for project in projects
        ]
    }), 200

@projects_bp.route("/archived", methods=["GET"])
@jwt_required()
def get_archived_projects():

    user_id = get_jwt_identity()

    projects = get_user_projects(
        user_id=user_id,
        status="ARCHIVED"
    )

    return jsonify({
        "projects": [
            {
                "id": project.id,
                "title": project.title,
                "description": project.description,
                "research_field": project.research_field,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
            for project in projects
        ]
    }), 200

@projects_bp.route("/<int:project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    project = get_project_by_id(project_id=project_id,user_id=user_id)
    if not project:
        return jsonify({
            "error": "Project not found"
        }), 404
    return jsonify({
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "research_field": project.research_field,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    }), 200 

@projects_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_project_route(project_id):

    user_id = get_jwt_identity()

    project = get_project_by_id(
        project_id=project_id,
        user_id=user_id
    )

    if not project:
        return jsonify({
            "error": "Project not found"
        }), 404

    data = request.get_json()

    project = update_project(
        project=project,
        title=data.get("title"),
        description=data.get("description"),
        research_field=data.get("research_field"),
        status=data.get("status")
    )

    return jsonify({
        "message": "Project updated successfully",
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "research_field": project.research_field,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    }), 200

@projects_bp.route("/<int:project_id>/archive", methods=["PATCH"])
@jwt_required()
def archive_project_route(project_id):

    user_id = get_jwt_identity()

    project = get_project_by_id(
        project_id=project_id,
        user_id=user_id
    )

    if not project:
        return jsonify({
            "error": "Project not found"
        }), 404

    project = archive_project(project)

    return jsonify({
        "message": "Project archived successfully",
        "project": {
            "id": project.id,
            "title": project.title,
            "status": project.status,
            "updated_at": project.updated_at.isoformat()
        }
    }), 200

@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project_route(project_id):
    user_id = get_jwt_identity()
    project = get_project_by_id( project_id=project_id, user_id=user_id )

    if not project:
        return jsonify({
            "error": "Project not found"
        }), 404
    delete_project(project)
    
    return jsonify({
        "message": "Project deleted successfully"
    }), 200
