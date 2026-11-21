from flask import Flask
from app.extensions import db, migrate, jwt
from app.routes import home_bp
from config import Config
from app.models.user import User
from app.models.project import Project
from app.models.paper import Paper
from app.models.chunk import Chunk
from app.routes.auth import auth_bp
from flask_cors import CORS
from app.routes.projects import projects_bp
from app.routes.papers import papers_bp
from app.routes.ai import ai_bp
from app.routes.evaluation import evaluation_bp


def create_app(config_overrides=None):
    app = Flask(__name__)

    app.config.from_object(Config)

    if config_overrides:      # used by the automated tests
        app.config.update(config_overrides)

    CORS(app)    # "Allow cross-origin requests to this application."

    db.init_app(app)

    migrate.init_app(app, db)

    jwt.init_app(app)

    app.register_blueprint(home_bp)

    app.register_blueprint(auth_bp)

    app.register_blueprint(projects_bp)

    app.register_blueprint(papers_bp)

    app.register_blueprint(ai_bp)

    app.register_blueprint(evaluation_bp)
    
    return app

