from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from flask_jwt_extended import create_access_token
def register_user(data):
    if not data:              # Check if request body exists
        return {
            "success": False,
            "message": "Request body is missing."
        }, 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return {
            "success": False,
            "message": "Username, email and password are required."
        }, 400

    existing_username = User.query.filter_by(username=username).first()
    if existing_username:
        return {
            "success": False,
            "message": "Username already exists."
        }, 409
    
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return {
            "success": False,
            "message": "Email already exists."
         }, 409
    
    password_hash = generate_password_hash(password)
    user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )

    db.session.add(user)
    db.session.commit()
    return {
        "success": True,
        "message": "User registered successfully."
    }, 201

def login_user(data):
    if not data:
        return {
            "success": False,
            "message": "Request body is missing."
        }, 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {
            "success": False,
            "message": "Email and password are required."
        }, 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return {
            "success": False,
            "message": "Invalid email or password."
        }, 401
    if not check_password_hash(user.password_hash, password):
        return {
            "success": False,
            "message": "Invalid email or password."
        }, 401

    access_token = create_access_token(
                        identity=str(user.id)
                    )

    return {
        "success": True,
        "message": "Login successful.",
        "access_token": access_token
    }, 200
