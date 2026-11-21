import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

# Kept for backwards compatibility; the real folder comes from Config.UPLOAD_FOLDER
UPLOAD_FOLDER = os.path.join("uploads", "papers")


def is_pdf(file):
    """True when the upload really starts with the PDF magic bytes."""
    head = file.stream.read(5)
    file.stream.seek(0)
    return head == b"%PDF-"


def save_paper_file(file):

    original_filename = secure_filename(file.filename) # our original file name like research_paper.pdf
    unique_filename = f"{uuid.uuid4()}_{original_filename}" # creating a unique name like "550e8400-e29b-41dresearch_paper.pdf"

    folder = current_app.config.get("UPLOAD_FOLDER", UPLOAD_FOLDER)
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, unique_filename)

    file.save(file_path)

    return original_filename, file_path
