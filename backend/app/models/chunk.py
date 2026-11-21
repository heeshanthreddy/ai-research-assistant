from app.extensions import db
from datetime import datetime


class Chunk(db.Model):
    """A semantic chunk of a paper, with its embedding (stored as float32 bytes).

    project_id is stored redundantly so that retrieval can always be filtered by
    project (and therefore by owner) without joining through papers.
    """
    __tablename__ = "chunks"

    id = db.Column(db.Integer, primary_key=True)

    paper_id = db.Column(
        db.Integer,
        db.ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    chunk_index = db.Column(db.Integer, nullable=False)   # order inside the paper
    page_start = db.Column(db.Integer, nullable=True)
    page_end = db.Column(db.Integer, nullable=True)
    text = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, nullable=False, default=0)

    embedding = db.Column(db.LargeBinary, nullable=True)
    embedding_backend = db.Column(db.String(150), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
