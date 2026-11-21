import os
from app.extensions import db
from app.models.paper import Paper


def create_paper(project_id,original_filename,file_path,file_size,title=None,authors=None,abstract=None,publication_year=None,  venue=None,doi=None):

    paper = Paper(
        project_id=project_id,
        title=title,
        authors=authors,
        abstract=abstract,
        publication_year=publication_year,
        venue=venue,
        doi=doi,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size
    )
    db.session.add(paper)
    db.session.commit()
    return paper

def get_project_papers(project_id):

    papers = Paper.query.filter_by( project_id=project_id ).all()
    return papers

def get_paper_by_id(paper_id, project_id):
    paper = Paper.query.filter_by( id=paper_id, project_id=project_id ).first()
    return paper

def delete_paper(paper):
    _remove_file(paper.file_path)
    db.session.delete(paper)
    db.session.commit()

def _remove_file(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def paper_to_dict(paper, with_chunk_count=True):
    return {
        "id": paper.id,
        "project_id": paper.project_id,
        "title": paper.title,
        "authors": paper.authors,
        "original_filename": paper.original_filename,
        "file_size": paper.file_size,
        "num_pages": paper.num_pages,
        "status": paper.status,
        "processing_error": paper.processing_error,
        "processing_warnings": paper.processing_warnings,
        "extraction_method": paper.extraction_method,
        "chunk_count": paper.chunks.count() if with_chunk_count else None,
        "created_at": paper.created_at.isoformat() if paper.created_at else None,
        "processed_at": paper.processed_at.isoformat() if paper.processed_at else None,
    }
