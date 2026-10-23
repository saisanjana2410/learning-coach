# Learning Coach

A personal learning and interview preparation agent. The application provides a React dashboard, persistent profiles and tutor conversations, rubric-based practice, weak-area tracking, and revision dates through FastAPI and SQLite.

## Run locally

Use Python 3.11 or newer and Node.js 22.12 or newer.

Backend, from the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements-dev.txt
Copy-Item backend/.env.example backend/.env
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001
```

Frontend, in a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the URL Vite prints, usually http://127.0.0.1:5173. Its development proxy connects `/api` to the backend on port 8001. API documentation is at http://127.0.0.1:8001/docs.

Store your OpenAI key only in `backend/.env`. It is not needed for this milestone. Never use a `VITE_` variable for secrets: those are included in browser code. Environment files, databases, virtual environments, generated previews, and node_modules are ignored by Git.

## Verify

```powershell
.\.venv\Scripts\python -m pytest
cd frontend
npm run build
```

The root pytest configuration supplies the backend import path.

The API is local and single-user. Do not expose it publicly without authentication. Tables are created on startup for this initial schema; introduce migrations before evolving persisted learning records. The private GitHub remote is configured as origin.

## Structure

- `backend/app`: API, validation, and profile persistence
- `backend/tests`: persistence and validation checks
- `frontend/src`: onboarding, dashboard, progress and styles
- `docs`: architecture Word document and generation script

Next: expand reviewed evaluation examples, add richer applied exercises, and extend the curriculum.

## Lessons and tutor

Open **Learn** to choose one of three starter lessons: predictions, coefficients, or residuals. Lessons are available without a key. Tutor chats are saved in SQLite and resume through **Continue learning**. Informal chat does not update progress; submit an answer in Practice for scored feedback and revision dates.

Set `OPENAI_API_KEY` in `backend/.env` and optionally `OPENAI_MODEL` (default: `gpt-4.1-mini`). Restart the backend after changing environment settings. The key is never sent to the browser. Tutor requests send the lesson, role, experience, study time, and recent conversation to OpenAI and incur API usage charges. No API requests are made merely by opening a lesson.

The tutor uses LangChain `create_agent` with read-only `get_lesson` and `get_learning_profile` tools. Output tokens, tool steps, provider retries, and request timeouts are bounded. Provider errors are replaced with a generic retry message. Failed requests preserve the submitted text; retries use the same message identifier. This implementation uses a process-local lock and is intended for one local backend worker.

Tests use an injected tutor response and do not contact OpenAI. `backend/requirements.lock.txt` records tested package versions; install it for a reproducible development environment.

## Scored practice and revision

The Practice view supports conceptual, applied, and interview explanation questions. Ten versioned questions cover five starter skills. Rubrics and reference answers remain server-side until feedback is accepted. Interview answers include a clarity criterion; applied questions are written scenarios, not executed code.

The evaluator returns structured criterion judgments, exact answer excerpts, strengths, gaps, and next steps. Python validates criterion coverage and evidence excerpts, then computes rubric points. Insufficient evidence is shown without a score and does not change the prior review schedule. Provider failures preserve the answer for an idempotent retry and never count as a learning failure.

Progress separates conceptual understanding, practical application, and interview explanation. Weak areas from any mode guide question selection. Reviews are scheduled 1 day after a score below 50, 2 days after a partial result, and 4 days after an independent correct answer. A fresh correct question at least 4 days after another correct answer in the same dimension establishes initial demonstrated proficiency and an 8-day review. A gap resets that evidence sequence. These are initial heuristics, not validated mastery estimates; future releases can extend the schedule and evaluate grading consistency on a larger reviewed set.

The database now has an additive `practice_attempts` table. Existing profiles and conversations are preserved. Accepted attempts retain the question and rubric snapshot, submitted answer, evaluator model, feedback and scheduling rule version. Progress and due dates are derived from accepted attempts; the database remains the source of truth across restarts. Reviews appear when the app opens; no proactive notifications are sent.

Practice endpoints: `POST /api/v1/practice/start`, `GET /api/v1/practice/current`, `POST /api/v1/practice/{id}/submit`, `POST /api/v1/practice/{id}/discard`, and `GET /api/v1/progress`. The tutor receives saved weak-area summaries to personalize explanations. Informal chat is not automatically graded.

## Commit conventions

Use descriptive conventional commit messages: `feat(practice): ...`, `fix(tutor): ...`, `test(revision): ...`, and `docs(setup): ...`. Explain the user-visible change in the subject.
