"""End-to-end API tests with the real Flask app, a temporary SQLite database and
the LEXICAL hashing embedder (deterministic, offline). They verify the plumbing
and the behaviour of every stage; they are functional tests, NOT benchmarks, and
they do not demonstrate semantic (MiniLM) quality."""
import io
import os
import tempfile
import unittest

from app import create_app
from app.extensions import db
from app.nlp import embeddings
from tests.make_test_pdf import build

try:
    import reportlab  # noqa: F401
    HAVE_REPORTLAB = True
except ImportError:
    HAVE_REPORTLAB = False


@unittest.skipUnless(HAVE_REPORTLAB, "reportlab not installed (pip install reportlab)")
class PipelineAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        embeddings.reset_embedder()
        cls.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + os.path.join(cls.tmp.name, "t.db"),
            "UPLOAD_FOLDER": os.path.join(cls.tmp.name, "uploads"),
            "EMBEDDING_BACKEND": "hashing",
            "JWT_SECRET_KEY": "test-secret-key-that-is-long-enough-0123456789",
        })
        with cls.app.app_context():
            db.create_all()
        cls.c = cls.app.test_client()
        cls.pdf_path = build(os.path.join(cls.tmp.name, "paper.pdf"))
        cls.h = cls._login("alice")
        cls.pid = cls.c.post("/api/projects/", json={"title": "P1"}, headers=cls.h).get_json()["project"]["id"]
        with open(cls.pdf_path, "rb") as fh:
            cls.upload = cls.c.post(f"/api/projects/{cls.pid}/papers", headers=cls.h,
                                    data={"file": (io.BytesIO(fh.read()), "paper.pdf")},
                                    content_type="multipart/form-data")

    @classmethod
    def tearDownClass(cls):
        embeddings.reset_embedder()
        with cls.app.app_context():
            db.session.remove()
            db.engine.dispose()
        try:
            cls.tmp.cleanup()
        except PermissionError:
            pass

    @classmethod
    def _login(cls, name):
        cls.c.post("/api/auth/register", json={"username": name, "email": f"{name}@x.com", "password": "pw123456"})
        tok = cls.c.post("/api/auth/login", json={"email": f"{name}@x.com", "password": "pw123456"}).get_json()["access_token"]
        return {"Authorization": "Bearer " + tok}

    def base(self, suffix=""):
        return f"/api/projects/{self.pid}{suffix}"

    # --- auth / ownership ---------------------------------------------------
    def test_01_auth_required(self):
        self.assertEqual(self.c.get(self.base("/papers")).status_code, 401)

    def test_02_upload_processed(self):
        self.assertEqual(self.upload.status_code, 201)
        paper = self.upload.get_json()["paper"]
        self.assertEqual(paper["status"], "PROCESSED", paper)
        self.assertEqual(paper["num_pages"], 3)
        self.assertGreaterEqual(paper["chunk_count"], 2)
        self.assertEqual(paper["title"], "Local Retrieval for Scientific Question Answering")

    def test_03_rejects_non_pdf(self):
        r = self.c.post(self.base("/papers"), headers=self.h, content_type="multipart/form-data",
                        data={"file": (io.BytesIO(b"hello world"), "x.pdf")})
        self.assertEqual(r.status_code, 415)
        r = self.c.post(self.base("/papers"), headers=self.h, content_type="multipart/form-data",
                        data={"file": (io.BytesIO(b"%PDF-1.4"), "x.txt")})
        self.assertEqual(r.status_code, 415)

    def test_04_corrupt_pdf_becomes_failed_not_crash(self):
        r = self.c.post(self.base("/papers"), headers=self.h, content_type="multipart/form-data",
                        data={"file": (io.BytesIO(b"%PDF-1.4 garbage"), "bad.pdf")})
        self.assertEqual(r.status_code, 201)
        paper = r.get_json()["paper"]
        self.assertEqual(paper["status"], "FAILED")
        self.assertTrue(paper["processing_error"])
        self.c.delete(self.base(f"/papers/{paper['id']}"), headers=self.h)

    def test_05_chunks_have_pages_and_clean_text(self):
        pid = self.c.get(self.base("/papers"), headers=self.h).get_json()["papers"][0]["id"]
        data = self.c.get(self.base(f"/papers/{pid}/chunks"), headers=self.h).get_json()
        chunks = data["chunks"]
        text = " ".join(c["text"] for c in chunks)
        self.assertNotIn("Running Header", text)                   # header removed
        # an intra-line hyphen is a real hyphen and must be preserved; joining of words
        # hyphenated across a LINE BREAK is covered by test_nlp_units.SentenceSplitting
        self.assertIn("hyphen-ation", text)
        # content survives extraction + cleaning intact (abbreviation/decimal handling is
        # asserted in test_nlp_units.SentenceSplitting)
        self.assertIn("Smith et al. reported 0.85 accuracy on Fig. 3 of their study.", text)
        self.assertTrue(all(c["page_start"] and c["page_end"] >= c["page_start"] for c in chunks))
        self.assertEqual({c["page_start"] for c in chunks} | {c["page_end"] for c in chunks} <= {1, 2, 3}, True)
        self.assertTrue(all(c["embedding_backend"] == "hashing:1024" for c in chunks))

    def test_06_ask_extractive_with_citations_and_verification(self):
        r = self.c.post(self.base("/ask"), headers=self.h, json={"question": "What does the verifier compare with the cited passage?"})
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual(d["method"], "extractive")
        self.assertFalse(d["insufficient_evidence"], d)
        self.assertRegex(d["answer"], r"\[\d+\]")
        self.assertTrue(d["sources"])
        s = d["sources"][0]
        for key in ("paper_title", "page_start", "chunk_id", "passage", "number"):
            self.assertIn(key, s)
        # every answer sentence must be copied from the retrieved passages (extractive guarantee)
        for sel in d["selected_sentences"]:
            self.assertTrue(any(sel["text"] in src["passage"] for src in d["sources"]))
        self.assertIn("verifier", d["answer"].lower())
        v = d["verification"]["metrics"]
        self.assertEqual(v["citation_coverage"], 1.0)
        self.assertEqual(v["citation_accuracy"], 1.0)

    def test_07_ask_unrelated_returns_insufficient(self):
        r = self.c.post(self.base("/ask"), headers=self.h, json={"question": "zebra quantum volcano spaghetti"})
        d = r.get_json()
        self.assertTrue(d["insufficient_evidence"])
        self.assertEqual(d["sources"], [])
        self.assertIn("not contain enough evidence", d["answer"])

    def test_08_open_cited_passage(self):
        d = self.c.post(self.base("/ask"), headers=self.h, json={"question": "How is recall at k defined?"}).get_json()
        cid = d["sources"][0]["chunk_id"]
        r = self.c.get(self.base(f"/chunks/{cid}"), headers=self.h)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["chunk"]["text"], d["sources"][0]["passage"])

    def test_09_verify_endpoint_flags_bad_citations(self):
        src = [{"number": 1, "passage": "Dense retrieval maps sentences to vectors."}]
        r = self.c.post(self.base("/verify"), headers=self.h, json={
            "answer": "Dense retrieval maps sentences to vectors [1]. The sky is purple [1]. No cite here. Ghost [4].",
            "sources": src})
        st = [s["status"] for s in r.get_json()["sentences"]]
        self.assertEqual(st, ["supported", "weak_support", "uncited", "invalid_citation"])

    def test_10_overlap_flags_copied_sentence_not_original(self):
        copied = "Mean reciprocal rank averages the inverse rank of the first relevant passage."
        original = "Penguins enjoy swimming in cold southern oceans every single morning."
        d = self.c.post(self.base("/overlap"), headers=self.h, json={"text": copied + " " + original}).get_json()
        flags = [s["flagged"] for s in d["sentences"]]
        self.assertEqual(flags, [True, False])
        self.assertEqual(d["sentences"][0]["match"]["page_start"], 2)
        self.assertIn("not a web-scale plagiarism detector", d["scope_note"])

    def test_11_idea_analysis(self):
        d = self.c.post(self.base("/idea"), headers=self.h,
                        json={"idea": "Entailment based verification of citations in retrieval systems"}).get_json()
        self.assertTrue(d["available"])
        self.assertEqual(len(d["closest_papers"]), 1)
        self.assertAlmostEqual(d["novelty_estimate"], 1 - d["average_similarity_closest"], places=3)
        self.assertNotIn("verdict", d)
        self.assertIn("relative", d["scope_note"].lower())
        gaps = d["possible_gaps"]
        self.assertIn("retrieval systems", gaps)                    # phrase absent from the paper
        self.assertNotIn("entailment based", gaps)                  # phrase present in the paper
        self.assertNotIn("based verification", gaps)

    def test_12_pair_classifier_is_untrained_and_makes_no_prediction(self):
        d = self.c.post("/api/nlp/pair-similarity", headers=self.h,
                        json={"text_a": "dense retrieval of papers", "text_b": "retrieval of dense papers"}).get_json()
        self.assertIsNone(d["prediction"])
        self.assertFalse(d["model"]["trained"])
        self.assertEqual(set(d["features"]), {"embedding_cosine", "tfidf_cosine", "jaccard", "length_ratio"})

    def test_13_retrieval_evaluation_endpoint_computes_from_supplied_labels(self):
        pid = self.c.get(self.base("/papers"), headers=self.h).get_json()["papers"][0]["id"]
        d = self.c.post(self.base("/evaluation/retrieval"), headers=self.h, json={
            "k": 3, "queries": [{"question": "mean reciprocal rank", "relevant_paper_ids": [pid]}]}).get_json()
        self.assertEqual(d["recall@3"], 1.0)
        self.assertEqual(d["mrr"], 1.0)
        self.assertEqual(d["evaluation_type"], "smoke test")

    def test_14_status_reports_lexical_fallback_honestly(self):
        d = self.c.get("/api/nlp/status", headers=self.h).get_json()
        self.assertFalse(d["embedding"]["semantic"])
        self.assertIn("LEXICAL", d["embedding"]["note"])
        self.assertFalse(d["qa"]["external_api"])

    def test_15_other_user_cannot_access_project(self):
        h2 = self._login("bob")
        for method, url, kw in [("get", self.base("/papers"), {}), ("post", self.base("/ask"), {"json": {"question": "x"}}),
                                ("post", self.base("/overlap"), {"json": {"text": "x"}}),
                                ("get", self.base("/chunks/1"), {})]:
            r = getattr(self.c, method)(url, headers=h2, **kw)
            self.assertEqual(r.status_code, 404, url)

    def test_16_empty_project_answers_insufficient(self):
        pid2 = self.c.post("/api/projects/", json={"title": "Empty"}, headers=self.h).get_json()["project"]["id"]
        d = self.c.post(f"/api/projects/{pid2}/ask", headers=self.h, json={"question": "anything at all?"}).get_json()
        self.assertTrue(d["insufficient_evidence"])

    def test_17_delete_paper_removes_chunks_and_file(self):
        pid = self.c.post("/api/projects/", json={"title": "Del"}, headers=self.h).get_json()["project"]["id"]
        with open(self.pdf_path, "rb") as fh:
            p = self.c.post(f"/api/projects/{pid}/papers", headers=self.h, content_type="multipart/form-data",
                            data={"file": (io.BytesIO(fh.read()), "d.pdf")}).get_json()["paper"]
        with self.app.app_context():
            from app.models.paper import Paper
            from app.models.chunk import Chunk
            path = Paper.query.get(p["id"]).file_path
            self.assertTrue(os.path.exists(path))
        self.assertEqual(self.c.delete(f"/api/projects/{pid}/papers/{p['id']}", headers=self.h).status_code, 200)
        with self.app.app_context():
            self.assertEqual(Chunk.query.filter_by(paper_id=p["id"]).count(), 0)
            self.assertFalse(os.path.exists(path))

    def test_18_no_external_api_dependency_in_source(self):
        root = os.path.join(os.path.dirname(__file__), "..", "app")
        banned = ("google.generativeai", "genai", "openai", "GEMINI", "api_key", "API_KEY")
        for dirpath, _, files in os.walk(root):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(dirpath, f), encoding="utf-8") as fh:
                        src = fh.read()
                    for b in banned:
                        self.assertNotIn(b, src, f"{b} found in {f}")


if __name__ == "__main__":
    unittest.main()
