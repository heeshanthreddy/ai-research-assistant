from app.extensions import db
from datetime import datetime


class Paper(db.Model):
    __tablename__ = "papers"

    id = db.Column( db.Integer, primary_key=True )

    project_id = db.Column( db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False )

    title = db.Column( db.String(300), nullable=True )

    authors = db.Column( db.Text, nullable=True )

    abstract = db.Column( db.Text, nullable=True )

    publication_year = db.Column( db.Integer, nullable=True )

    venue = db.Column( db.String(300), nullable=True )

    doi = db.Column( db.String(255), nullable=True )

    original_filename = db.Column( db.String(255), nullable=False )

    file_path = db.Column( db.String(500), nullable=False )

    file_size = db.Column( db.Integer, nullable=False )

    extracted_text = db.Column( db.Text, nullable=True )

    status = db.Column( db.String(20), nullable=False, default="UPLOADED" )

    processing_error = db.Column( db.Text, nullable=True )

    processed_at = db.Column( db.DateTime, nullable=True )

    created_at = db.Column( db.DateTime, default=datetime.utcnow, nullable=False )

    updated_at = db.Column( db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False )

    # --- added for the local NLP pipeline -----------------------------------
    num_pages = db.Column( db.Integer, nullable=True )

    extraction_method = db.Column( db.String(50), nullable=True )

    processing_warnings = db.Column( db.Text, nullable=True )

    chunks = db.relationship( "Chunk", backref="paper", cascade="all, delete-orphan", lazy="dynamic" )
