from flask import Blueprint, jsonify
#    Blueprint → to organize routes.
#    jsonify → to return JSON responses instead of HTML.
from flask import request
from app.services.auth_service import register_user, login_user
from flask_jwt_extended import jwt_required, get_jwt_identity

auth_bp = Blueprint( "auth", __name__, url_prefix="/api/auth" )

@auth_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "message": "Authentication service is running."
    }), 200

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    response, status = register_user(data)
    return jsonify(response), status

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    response, status = login_user(data)
    return jsonify(response), status

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    return jsonify({
        "success": True,
        "message": "Protected route accessed successfully.",
        "user_id": current_user_id
    }), 200