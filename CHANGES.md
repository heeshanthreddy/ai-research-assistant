# ResearchForge - repair report

The original project was a skeleton: working JWT auth and project CRUD, but **no NLP code at all**. `rag_service.py`, `ai_service.py`, `routes/ai.py`, `routes/evaluation.py` were empty, the upload route returned the text `NEW PAPER ROUTE`, and Chroma, MiniLM, MMR, citation verification, the classifier and evaluation did not exist anywhere in the code. So most of this work is **new implementation inside the existing architecture**, not repair of existing NLP code. Gemini appeared only as unused entries in `requirements.txt` (no source file used it) and has been removed.

The original project was not modified: work was done on a copy.

## Bugs found in the original
- Frontend imports `./components/Navbar` and `../services/authService`, but the files were `navbar.jsx` / `authservice.js`: **build breaks on Linux/macOS** (works on Windows). Files renamed to match the imports.
- Refreshing any protected page logged the user out (auth state started `false`). Fixed.
- `flask_cors` is imported but was missing from `requirements.txt`. Added.
- Register page was a stub with no API call; Login showed no errors.
- Upload route was a stub. `tempCodeRunnerFile.py` (editor artefact) removed.
- `api_test.http` contained live-looking JWT tokens: replaced by a token-free version. **Rotate any token that was in that file.**

## Modified files
| File | Why |
|---|---|
| `backend/config.py` | local NLP settings (all env-overridable), upload folder, safe defaults, SQLite fallback |
| `backend/requirements.txt` | removed Gemini/Google libraries; added `flask-cors`, `numpy`, `scikit-learn` |
| `backend/app/__init__.py` | register new blueprints; `create_app(config_overrides)` for tests |
| `backend/app/models/paper.py`, `project.py` | pages/method/warnings columns; cascade relationships |
| `backend/app/routes/papers.py` | real upload (PDF magic-byte check), list, detail, delete, chunks, open passage, re-index |
| `backend/app/routes/ai.py`, `evaluation.py` | ask, verify, idea, overlap, pair similarity, NLP status, retrieval evaluation |
| `backend/app/services/paper_service.py`, `project_service.py` | `paper_to_dict`, file clean-up on delete |
| `backend/app/services/ai_service.py`, `rag_service.py` | still placeholders; now document where the logic lives |
| `backend/app/utils/file_storage.py` | PDF magic-byte check, absolute upload folder |
| `backend/api_test.http` | tokens removed, new endpoints |
| `frontend/src/App.jsx`, `main.jsx`, `context/AuthContext.jsx`, `services/api.js` | workspace route, stylesheet, refresh fix, 401 handling, readable errors |
| `frontend/src/pages/Login.jsx`, `Register.jsx`, `Dashboard.jsx` | error display, real registration, project list/create/delete |
| `frontend/src/styles/global.css` | styles (file existed but was empty) |
| `.gitignore`, `README.md` | submission-ready |

## New files
- Backend NLP package: `app/nlp/{pdf_extraction,preprocessing,chunking,embeddings,vector_store,retrieval,qa,citations,idea_analysis,overlap,classifier,metrics,stopwords}.py`
- `app/models/chunk.py`, `app/services/processing_service.py`, `app/routes/_helpers.py`
- Migration `migrations/versions/c41d9e7a2b10_add_chunks_and_paper_nlp_fields.py`
- `scripts/smoke_test.py`, `scripts/train_pair_classifier.py`
- Tests: `tests/{test_nlp_units,test_pdf_extraction,test_embedder_selection,test_api_pipeline,make_test_pdf}.py`
- `backend/.env.example`, `backend/requirements-semantic.txt`, `backend/requirements-dev.txt`, `frontend/.env.example`
- Frontend: `pages/ProjectWorkspace.jsx`, `components/{StatusBanner,PapersPanel,AskPanel,IdeaPanel,OverlapPanel,PairPanel}.jsx`, `services/researchService.js` (+ renamed `Navbar.jsx`, `authService.js`)

## Files that remain incomplete (empty in the original, not needed for the core pipeline)
`app/models/{draft,evaluation,note}.py`, `app/routes/notes.py`, `frontend/src/components/{buttons,input,sidebar}.jsx`, `frontend/src/styles/auth.css`. `backend/data/`, `docs/`, `notebooks/`, `training/` are empty directories.

## Test results (actually executed)
**Passed - backend, 45 tests** (`python -m unittest discover -s tests -t .`): 16 NLP unit tests, 5 embedder selection/fallback, 6 PDF extraction, 18 API pipeline tests.
**Passed - frontend**: ESLint clean; all 42 relative imports resolve on a case-sensitive file system (the original had 3 unresolved); bundle compiles with esbuild; **19 browser checks in headless Chromium** against the live backend (logged-out redirect, bad-login error, register, login, refresh keeps session, create project, status banner, upload -> PROCESSED, chunk viewer, answer with `[1]`, "extractive" label, open cited passage, verification table, accuracy/coverage, insufficient-evidence message, idea analysis, overlap flags only the copied sentence, pair classifier reports untrained, logout).
**Passed - database**: `flask db upgrade` from empty SQLite through all 4 migrations; `flask db check` reports no model/migration drift.
**Failed**: none in the final run. Two real bugs were found by the tests during development and fixed in code (running headers were not removed because the repeated-line check ran after line joining; the lexical embedder matched unrelated sentences on stop-words). Two test assertions were corrected because their premise was wrong, not the code.

**NOT run** (no network / different OS in the author's sandbox) - please check on your machine:
- real **PyMuPDF** extraction (tests used a stand-in `fitz` for the logic and `pypdf` for a real PDF) -> run `python scripts/smoke_test.py your_paper.pdf`
- real **MiniLM** model (wrapper tested through a stand-in; semantic quality unmeasured)
- **PostgreSQL** (tests used SQLite), migration downgrade, Python 3.14
- `npm install`, `npm run dev`, `vite build` (bundle was built with esbuild instead)
- All tests use a **synthetic** PDF written for testing, not a real research paper, and the lexical embedder.

## Implemented vs future work
**Implemented:** see the table in README section 1.
**Future work:** ChromaDB backend, Phase 5 quality scorer, OCR, NLI-based faithfulness, STS-Benchmark evaluation, hand-labelled retrieval benchmark, chunking ablation, background workers, notes/drafts.

## Differences from the presentation (update the slides)
- No ChromaDB: vectors are in SQL + exact NumPy cosine scan.
- No Gemini / LLM generator: answering is extractive only.
- Authentication is a JWT in the Authorization header (not an HttpOnly cookie + CSRF).
- No Phase 5 quality scorer.
- Thresholds are configurable engineering defaults (README section 3); chunk size 40/220 and 18/6/0.7 retrieval defaults come from the earlier design notes and are untuned.
- "26 automated tests" in the old deck no longer applies: the suite now has 45 backend tests plus the browser run described above.

## Screenshots to capture from YOUR real run (with a real paper)
1. Registration/login page.
2. Dashboard with a project.
3. Papers tab after upload, showing `PROCESSED`, page and chunk counts.
4. Chunk viewer showing chunks with page ranges.
5. Ask tab: extractive answer with `[n]` markers and the "extractive" label.
6. A source passage opened by clicking `[n]`.
7. Citation verification table with accuracy/coverage.
8. The "insufficient evidence" answer for an off-topic question.
9. Idea analysis result (closest papers + possible gaps).
10. Overlap result with a flagged sentence and its matching passage.
11. The status banner in MiniLM mode (semantic) if you install it.
