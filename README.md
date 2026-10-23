# Learning Coach

A personal learning and interview preparation agent. The first milestone provides a React dashboard, onboarding, and a persistent learning profile through FastAPI and SQLite. Tutor conversations, assessments, and revision scheduling are next; dashboard counts currently represent an unassessed learner.

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

The API is local and single-user. Do not expose it publicly without authentication. Tables are created on startup for this initial schema; introduce migrations before evolving persisted learning records. No remote Git repository has been configured.

## Structure

- `backend/app`: API, validation, and profile persistence
- `backend/tests`: persistence and validation checks
- `frontend/src`: onboarding, dashboard, progress and styles
- `docs`: architecture Word document and generation script

Next: reviewed linear regression content, LangChain tutor with OpenAI, answer evaluation, and shared weak-area tracking.

## Lessons and tutor

Open **Learn** to choose one of three starter lessons: predictions, coefficients, or residuals. Lessons are available without a key. Tutor chats are saved in SQLite and resume through **Continue learning**. These chats do not yet update mastery, weak areas, or review dates.

Set `OPENAI_API_KEY` in `backend/.env` and optionally `OPENAI_MODEL` (default: `gpt-4.1-mini`). Restart the backend after changing environment settings. The key is never sent to the browser. Tutor requests send the lesson, role, experience, study time, and recent conversation to OpenAI and incur API usage charges. No API requests are made merely by opening a lesson.

The tutor uses LangChain `create_agent` with read-only `get_lesson` and `get_learning_profile` tools. Output tokens, tool steps, provider retries, and request timeouts are bounded. Provider errors are replaced with a generic retry message. Failed requests preserve the submitted text; retries use the same message identifier. This implementation uses a process-local lock and is intended for one local backend worker.

Tests use an injected tutor response and do not contact OpenAI. `backend/requirements.lock.txt` records tested package versions; install it for a reproducible development environment.
