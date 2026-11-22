"""Run the whole local pipeline on a REAL PDF using a throw-away SQLite database.

    cd backend
    python scripts/smoke_test.py path/to/paper.pdf "What problem does the paper address?"

It uses whatever EMBEDDING_BACKEND your .env selects (auto -> MiniLM if installed,
otherwise the lexical hashing fallback) and the real PyMuPDF extractor if it is
installed. Nothing is written to your real database or uploads folder.
This is a functional smoke test, not an accuracy evaluation.
"""
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app          # noqa: E402
from app.extensions import db       # noqa: E402


def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        sys.exit(__doc__)
    pdf = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "What is the main contribution of this paper?"

    tmp = tempfile.TemporaryDirectory()
    app = create_app({"TESTING": True,
                      "SQLALCHEMY_DATABASE_URI": "sqlite:///" + os.path.join(tmp.name, "smoke.db"),
                      "UPLOAD_FOLDER": os.path.join(tmp.name, "uploads")})
    with app.app_context():
        db.create_all()
    c = app.test_client()
    c.post("/api/auth/register", json={"username": "smoke", "email": "smoke@example.com", "password": "smoke-pass-123"})
    tok = c.post("/api/auth/login", json={"email": "smoke@example.com", "password": "smoke-pass-123"}).get_json()["access_token"]
    h = {"Authorization": "Bearer " + tok}
    pid = c.post("/api/projects/", json={"title": "Smoke test"}, headers=h).get_json()["project"]["id"]

    status = c.get("/api/nlp/status", headers=h).get_json()
    print("EMBEDDING :", status["embedding"]["backend"], "-", status["embedding"]["note"])
    if status["embedding"].get("fallback_reason"):
        print("            reason:", status["embedding"]["fallback_reason"])

    with open(pdf, "rb") as fh:
        r = c.post(f"/api/projects/{pid}/papers", headers=h, content_type="multipart/form-data",
                   data={"file": (io.BytesIO(fh.read()), os.path.basename(pdf))})
    paper = r.get_json()["paper"]
    print(f"PAPER     : status={paper['status']} extractor={paper['extraction_method']} pages={paper['num_pages']} "
          f"chunks={paper['chunk_count']}\n            title={paper['title']!r}")
    if paper["processing_warnings"]:
        print("            warnings:", paper["processing_warnings"])
    if paper["status"] != "PROCESSED":
        sys.exit("FAILED: " + str(paper["processing_error"]))

    chunks = c.get(f"/api/projects/{pid}/papers/{paper['id']}/chunks", headers=h).get_json()["chunks"]
    print("CHUNK 0   :", chunks[0]["text"][:200].replace("\n", " "), "...")

    ans = c.post(f"/api/projects/{pid}/ask", json={"question": question}, headers=h).get_json()
    print("\nQUESTION  :", question)
    print("ANSWER    :", ans["answer"])
    for s in ans["sources"]:
        print(f"   [{s['number']}] {s['paper_title']} p.{s['page_start']}-{s['page_end']} chunk {s['chunk_id']}")
    if ans.get("verification"):
        print("VERIFY    :", json.dumps({k: ans["verification"]["metrics"][k] for k in
              ("citation_accuracy", "citation_coverage", "threshold")}))
    tmp.cleanup()


if __name__ == "__main__":
    main()
