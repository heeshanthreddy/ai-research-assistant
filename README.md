# ResearchForge

**An NLP-based research assistant for citation-grounded question answering and semantic research analysis.**

Upload research papers (PDF), then ask questions and get **extractive answers with numbered citations** that point back to a page and passage of your own papers. The citations are then checked automatically. Everything runs **locally**: there is **no external LLM, no cloud AI service and no API key**.

> **Honest scope.** This project does *extractive* question answering (answer sentences are copied from your papers). It is **not** a generative chatbot. Embedding similarity is a *proxy* for meaning, not proof of logical support. Novelty and overlap results are *relative to the papers you uploaded*. See [Known limitations](#known-limitations).

---

## 1. What is implemented (and how it was checked)

| Feature | Status |
|---|---|
| Register / login (JWT), projects (create, list, delete), owner-only access | Implemented, automated tests |
| PDF upload with real-PDF check, extraction with page numbers (PyMuPDF) | Implemented; PyMuPDF path not run by the author's test environment (see §8) |
| Cleaning (hyphenation, ligatures, page numbers, running headers) and rule-based sentence splitting (abbreviations, decimals, initials) | Implemented, unit tests |
| Semantic chunking (TextTiling-style on sentence embeddings, min/max size) | Implemented, unit tests |
| Local embeddings: `all-MiniLM-L6-v2` (CPU) **or** lexical hashing fallback | MiniLM wrapper implemented, **not executed** by the author (no network); hashing fallback tested |
| Vector storage and exact cosine search, filtered by project/owner | Implemented (SQL + NumPy), tests |
| MMR re-ranking (cosine similarity, configurable λ) | Implemented, unit tests |
| Extractive QA with `[n]` citations, relevance cut-off, "insufficient evidence" answer | Implemented, API + browser tests |
| Citation verification (supported / weak support / invalid citation / uncited), citation accuracy and coverage | Implemented, tests |
| Research idea analysis (closest papers, corpus-relative novelty indicator, possible gaps) | Implemented, tests; **not validated** against expert judgement |
| Semantic overlap detection against your own papers (two-stage: chunks, then sentences) | Implemented, tests |
| Passage-pair classifier (4 features + Logistic Regression) | Code implemented; **untrained and unvalidated** (no labelled dataset ships with the project) |
| Retrieval evaluation endpoint (Recall@k, MRR, nDCG) | Implemented; computes only from labelled queries **you** supply |
| React UI for the whole workflow | Implemented, browser test (headless Chromium) |

**Not implemented / future work:** ChromaDB integration, a Phase 5 "quality scorer", OCR for scanned PDFs, NLI-based faithfulness checking, STS-Benchmark evaluation, a hand-labelled retrieval benchmark, chunking ablation study, background workers for large uploads, notes/drafts modules (empty placeholders in the original project).

---

## 2. Architecture

```
React + Vite (frontend/)  --HTTP/JSON-->  Flask API (backend/app/routes)
                                              |
        auth (JWT)  projects  papers  ai (ask/verify/idea/overlap)  evaluation
                                              |
                              app/services  (project, paper, processing)
                                              |
                    app/nlp  (pdf_extraction, preprocessing, chunking, embeddings,
                              vector_store, retrieval, qa, citations,
                              idea_analysis, overlap, classifier, metrics)
                                              |
                       SQLAlchemy models: users, projects, papers, chunks
                       (PostgreSQL as originally configured, or SQLite fallback)
```

The original architecture (Flask, SQLAlchemy models, JWT auth, React + Vite) is kept. New: the `chunks` table (+ Alembic migration `c41d9e7a2b10`), the `app/nlp` package, the papers/ai/evaluation routes and the project workspace UI.

## 3. NLP pipeline

1. **PDF extraction** (`pdf_extraction.py`): PyMuPDF, per-page text, metadata title (fallback: largest font on page 1). Pages without a text layer are reported as warnings; a PDF with no text at all is rejected with a clear message (**OCR is not enabled**).
2. **Preprocessing** (`preprocessing.py`): ligatures, line-end hyphenation, stand-alone page numbers, repeated headers/footers (short lines on at least half of the pages, for documents of 3+ pages), sentence splitting that protects `et al.`, `Fig.`, `e.g.`, decimals and initials. Every sentence keeps its page.
3. **Semantic chunking** (`chunking.py`): embed sentences, compare the mean embedding of the 3 sentences before/after each gap, cut where similarity < mean − 0.5·std, split chunks above 220 words at their weakest gap, merge chunks below 40 words into the more similar neighbour. Sentences are never cut. *(These defaults come from the project design notes, are configurable, and are not tuned on a benchmark.)*
4. **Embeddings** (`embeddings.py`): `sentence-transformers/all-MiniLM-L6-v2` on CPU if installed, otherwise a **hashing embedder** (signed hashing of content-word uni/bi-grams). The hashing embedder is **lexical, not semantic**; the UI shows a warning banner whenever it is active.
5. **Vector storage / retrieval** (`vector_store.py`, `retrieval.py`): vectors are stored in the `chunks` table; search is an exact cosine scan limited to one project. Vectors from different embedders are never mixed (the "Re-index" button re-embeds a project after you switch embedder).
6. **MMR**: `λ·sim(q,d) − (1−λ)·max sim(d, selected)` on cosine similarities (no distance conversion anywhere). Defaults: 18 candidates, keep 6, λ = 0.7.
7. **Extractive QA** (`qa.py`): retrieve passages → split into sentences → rank sentences by similarity to the question → keep the best (up to 3, at least 50 % of the best score, no near-duplicates) → append `[n]` citations. If the best sentence is below the relevance floor the answer is *"The uploaded papers do not contain enough evidence…"*.
8. **Citation verification** (`citations.py`): normalise `claim. [1]` → `claim [1].`, then for each answer sentence compare with the sentences of the cited passage. Statuses: `supported`, `weak_support`, `invalid_citation` (marker without source), `uncited`. *Citation accuracy* = supported / cited sentences. *Citation coverage* = cited sentences / all answer sentences (the code cannot tell which sentences are "factual", so all are counted).

> Because extractive answers are copied from the sources, verification of the app's own answers is nearly guaranteed to pass; it mainly confirms that each marker points at the right passage. The verifier is also available for arbitrary text through `POST /api/projects/<id>/verify`.

### Thresholds you should know about (all configurable in `.env`)

These are **engineering defaults, not tuned values**. Cosine ranges differ a lot between MiniLM and the lexical embedder, hence separate values:

| Setting | MiniLM (semantic) | Hashing (lexical) |
|---|---|---|
| Citation "supported" threshold | 0.60 | 0.50 |
| QA minimum best-sentence score | 0.25 | 0.10 |
| Overlap flag threshold | 0.85 | 0.60 |

Change them with `CITATION_THRESHOLD_SEMANTIC`, `QA_MIN_SCORE_LEXICAL`, `OVERLAP_THRESHOLD_SEMANTIC`, etc. (see `backend/config.py`). Tune them on your own labelled examples before drawing conclusions.

### Idea analysis, without invented formulas
`S` = mean cosine similarity of the closest papers (each paper = normalised mean of its chunk vectors). The API returns `S` and `novelty_estimate = 1 − S`. **No normalisation and no verdict thresholds are applied.** Possible gaps are content-word bigrams of the idea that occur in none of the uploaded texts. All of it is relative to the uploaded corpus.

## 4. Technologies

Backend: Python, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), Flask-JWT-Extended, Flask-CORS, PyMuPDF, NumPy, scikit-learn, (optional) sentence-transformers. Frontend: React 19, Vite, React Router, Axios. Database: PostgreSQL (original) or SQLite (fallback).

## 5. Setup

Requirements: Python 3.10+ (3.11 or 3.12 recommended if you want MiniLM), Node.js 20+.

### Backend
```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate        macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # Windows: copy .env.example .env   -> then edit the values
```
Database: with `DATABASE_URL` unset the app uses a local SQLite file. For PostgreSQL set
`DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/researchforge` in `.env`.

```bash
flask --app run db upgrade     # creates/updates the tables (users, projects, papers, chunks)
python run.py                  # API on http://127.0.0.1:5000
```

### Optional: semantic MiniLM embeddings
```bash
pip install -r requirements-semantic.txt
```
The first run downloads the ~90 MB model once from the Hugging Face hub (no key needed), then works offline. If installation fails (PyTorch wheels can lag behind very new Python versions) use Python 3.11/3.12. Choose the mode in `.env`: `EMBEDDING_BACKEND=auto` (default; MiniLM if it loads, otherwise hashing), `minilm` (fail loudly if unavailable) or `hashing`. After changing the embedder click **Re-index project** in the UI (or `POST /api/projects/<id>/reindex`).

### Frontend
```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173
```
If the backend is not at `http://127.0.0.1:5000` create `frontend/.env` from `frontend/.env.example`.

## 6. Using the application

1. **Register**, then **log in**.
2. Create a **project** on the dashboard and open it.
3. **Papers** tab: upload a PDF. Status moves to `PROCESSED` (or `FAILED` with the reason). Use *View chunks* to inspect the semantic chunks with their page ranges.
4. **Ask** tab: type a question. You get an *extractive* answer with `[n]` markers; click a marker to open the cited passage; the citation-verification table shows each sentence's status and the accuracy/coverage numbers.
5. **Idea analysis**, **Overlap** and **Pair similarity** tabs use the same local embeddings.

A command-line check on a real PDF (uses a throw-away database):
```bash
cd backend
python scripts/smoke_test.py path/to/paper.pdf "What problem does the paper address?"
```

## 7. Passage-pair classifier (optional)
No labelled dataset is bundled, so the classifier is **untrained** and the API returns only the feature values (embedding cosine, TF-IDF cosine, Jaccard, length ratio). To train it you must supply a real labelled CSV (`text_a,text_b,label`, label 1 = similar):
```bash
python scripts/train_pair_classifier.py path/to/labelled_pairs.csv
```
Reported precision/recall/F1 come from a held-out 30 % split of *your* file only and are not benchmark (e.g. STS-B) results.

## 8. Tests

```bash
cd backend
pip install -r requirements-dev.txt      # reportlab, only to build a synthetic test PDF
python -m unittest discover -s tests -t . -v
```
Covered: sentence splitting, cleaning, chunking, MMR, metrics, citations, embedder selection/fallback, PDF extraction logic, and an API pipeline test (register, login, project, upload, extraction, chunks, retrieval, extractive QA, verification, overlap, idea analysis, pair classifier status, ownership isolation, deletion).

What the tests are **not**: they use a *synthetic* test PDF written for the tests (not a real research paper), run with the lexical hashing embedder, and are functional tests, **not benchmark evaluation**. Things the author could not run in an offline sandbox and you should check on your machine: the real PyMuPDF extractor (run `scripts/smoke_test.py` with a real paper), the real MiniLM model, PostgreSQL, and `npm run dev`/`vite build`.

## 9. Known limitations
- Extractive answers can only restate sentences that exist in the papers; they can still surface a sentence that is related to, but does not answer, the question.
- Cosine similarity ≠ entailment: negation, numbers and conditions can be missed.
- The hashing fallback compares words, not meaning; use MiniLM for semantic behaviour.
- Scanned PDFs without a text layer are rejected (no OCR). Two-column layouts may interleave columns depending on the PDF.
- Processing is synchronous (fine for papers of normal size; long PDFs make the upload request slow).
- Thresholds and chunk parameters are untuned defaults.
- Novelty and gap results are heuristics relative to the uploaded corpus, not proof of global novelty.
- Exact brute-force search is used instead of ChromaDB (fine for hundreds to a few thousand chunks).

## 10. Security notes
Never commit `.env`, tokens or uploaded papers (all in `.gitignore`). `JWT_SECRET_KEY` / `SECRET_KEY` have insecure development fallbacks: set real values in `.env`. If a JWT or password was ever committed or shared (for example in an old `api_test.http`), rotate it.

## 11. Project structure
```
backend/   app/{models,routes,services,nlp,utils}  config.py  run.py  migrations/  scripts/  tests/
frontend/  src/{pages,components,services,context,styles}
```
