# Learning Coach

A personal learning and interview preparation agent. The application provides a React dashboard, persistent profiles and tutor conversations, rubric-based practice, weak-area tracking, and revision dates through FastAPI and SQLite.

The current release focuses on **Python for ML → MLOps basics → a guided delivery-time prediction project**. All other modules remain visible as **Coming soon**, with earlier starter lessons still accessible. The focused path includes 12 authored lessons and 48 assessment tasks across four levels, plus a downloadable runnable project kit. Reading lessons and running the local project do not use OpenAI API tokens; tutor chats and answer feedback do.

Open **Guided project** to save milestone drafts and resume your work. Each level has its own workspace with six milestones: data, baseline, training, evaluation, deployment and monitoring. Save drafts locally without an API call; request feedback when ready. Submitted versions remain immutable, retries reuse saved answers, and feedback contributes to the existing weak-area/revision tracker with links to relevant lessons. Save before leaving the workspace; moving between milestones saves changes to the current draft. A milestone meets requirements only when its latest accepted feedback meets every rubric criterion. This is AI review of submitted text, not code execution or a mastery certificate.

**Tech updates** provides a manually refreshed, cached digest from official Python, scikit-learn, MLflow, PyTorch, Hugging Face Transformers and OpenAI feeds. Up to five relevant recent announcements include original links, source dates, learning suggestions and related foundations. Save a snapshot to revisit later. Refresh defaults to source excerpts without model usage. AI summaries require explicitly checking the option and use the backend OpenAI key; unchanged AI digests are reused. Opening the section makes no feed or model requests. Source failures and stale digests are identified, and a failed refresh preserves the previous digest. This is a curated feed digest, not exhaustive news coverage or a claim that every item was published today.

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

Development requirements include the NumPy/pandas/scikit-learn dependencies used by the project and its checks. When using the older backend lock file instead of development requirements, also install `examples/ml_project/requirements.txt`. Project setup, milestone instructions and optional local MLflow tracking are in [the project README](examples/ml_project/README.md).

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

The Practice view supports conceptual, applied, and interview explanation questions. Sixteen versioned questions cover linear regression plus starter Python, SQL, and classification interview skills. Rubrics and reference answers remain server-side until feedback is accepted. Interview answers include a clarity criterion; applied questions are written scenarios, not executed code.

The evaluator returns structured criterion judgments, exact answer excerpts, strengths, gaps, and next steps. Python validates criterion coverage and evidence excerpts, then computes rubric points. Insufficient evidence is shown without a score and does not change the prior review schedule. Provider failures preserve the answer for an idempotent retry and never count as a learning failure.

Progress separates conceptual understanding, practical application, and interview explanation. Weak areas from any mode guide question selection. Reviews are scheduled 1 day after a score below 50, 2 days after a partial result, and 4 days after an independent correct answer. A fresh correct question at least 4 days after another correct answer in the same dimension establishes initial demonstrated proficiency and an 8-day review. A gap resets that evidence sequence. These are initial heuristics, not validated mastery estimates; future releases can extend the schedule and evaluate grading consistency on a larger reviewed set.

The database now has an additive `practice_attempts` table. Existing profiles and conversations are preserved. Accepted attempts retain the question and rubric snapshot, submitted answer, evaluator model, feedback and scheduling rule version. Progress and due dates are derived from accepted attempts; the database remains the source of truth across restarts. Reviews appear when the app opens; no proactive notifications are sent.

Practice endpoints: `POST /api/v1/practice/start`, `GET /api/v1/practice/current`, `POST /api/v1/practice/{id}/submit`, `POST /api/v1/practice/{id}/discard`, and `GET /api/v1/progress`. The tutor receives saved weak-area summaries to personalize explanations. Informal chat is not automatically graded.

## Commit conventions

Use descriptive conventional commit messages: `feat(practice): ...`, `fix(tutor): ...`, `test(revision): ...`, and `docs(setup): ...`. Explain the user-visible change in the subject.


## Continuous learning and focused help

Topic practice starts from the linear regression module and keeps its conceptual or applied activity on Next question. There is no question limit. Switch activities inside the module, skip a question, or choose Finish for now. Active sessions resume after refresh, including accepted feedback. Starting from a lesson carries its skill into the first question.

Role interview is a separate entry point spanning the starter ML, Python and SQL bank. The saved target role labels the session; this is a limited starter bank, not comprehensive role coverage or automatic job-description matching. Topic sessions cannot select questions outside their module.

Finish for now saves a summary of answered and skipped questions, strengths, gaps encountered, covered skills and revision dates. Summaries and earlier question discussions remain accessible in Your progress. Repeated questions can appear after exhausting the finite bank.

Help me understand this opens a focused discussion beside accepted feedback (below it on small screens). The model receives only that question, its submitted answer, reference and feedback, and its own discussion history. It has no learning-profile or other-question tools. Help never modifies the original score or review dates. Failed messages are retained for retry, and duplicate retries do not duplicate replies.

Additive tables `learning_runs` and `question_discussions` preserve existing profiles, attempts and chats. Run membership is recorded in the attempt's question snapshot. The earlier pending single-question attempt is adopted when its mode matches a new run. This remains a local single-worker app; a shared deployment needs authentication, migrations, and cross-process concurrency controls.

New endpoints include `/api/v1/runs/current`, `/runs/start`, `/runs/{id}/next`, `/runs/{id}/finish`, `/runs/history`, and GET/POST `/api/v1/practice/{id}/help` (all run routes also use the `/api/v1` prefix).


## Curriculum and module levels

Modules now groups the learning path into Python, machine learning, math and statistics, deep learning, AI and LLM applications, and ML engineering. Role suggestions use curated templates based on the target role in Learning profile. An actual job description is not analyzed yet. Planned curriculum entries are explicitly labeled and cannot start empty practice sessions.

Four submodules have starter content at all three levels: Python functions, Python collections and iteration, linear regression, and model evaluation. The bank contains 14 short lessons and 38 questions, including fresh transfer questions. NumPy, pandas, broader supervised and unsupervised algorithms, deep learning, and other catalog entries remain planned. This is a usable curriculum foundation, not a complete course.

Each module has its own beginner, intermediate, or advanced preference. Until explicitly chosen it inherits the profile experience level. Changing a level changes the lesson focus and question bank. For example, Python functions covers return values, safe defaults, or closure binding at the respective levels. Preferences do not assert mastery or change past scores.

A new practice run snapshots its level and the module-level interview preferences. Changing preferences affects new runs without changing an active one. Topic runs stay within their submodule and level; role interviews combine banks at the chosen level for each module. Starting an explicit revision from progress may use the original question level. Existing profiles, lessons, attempts, and question discussions are retained.

The additive tables are `module_preferences` and `run_preferences`. `GET /api/v1/curriculum` returns suggestions, prerequisites, available content and planned entries. `PUT /api/v1/curriculum/{module_id}/level` saves a preference. `GET /api/v1/lessons?submodule_id=...&level=...` retrieves the matching lessons. Content metadata uses stable module, submodule, level and lesson identifiers; the legacy unfiltered lesson endpoint remains compatible.

Next priorities remain job-description mapping, a human-reviewed feedback evaluation set, and dated technology updates. None of those is represented as a completed feature. Source references for the starter concepts include the official Python tutorial at https://docs.python.org/3/tutorial/ and scikit-learn evaluation documentation at https://scikit-learn.org/stable/modules/cross_validation.html.

## Submodule navigation

Topic practice is entered from its submodule or lesson, not a separate sidebar destination. The selected submodule and level carry into practice without another submodule picker. Back to submodule returns to the matching curriculum section. Revision links enter the relevant practice directly; Role interview remains separate.


## Job description learning priorities

Job target lets you paste a description and title, then analyze explicit technical skills using OpenAI structured output. Every skill includes required, preferred or unspecified importance and an exact source excerpt. The extractor has one bounded repair attempt for invalid quotes; unsupported excerpts and duplicate names cannot be saved as valid analysis. The pasted description is sent to OpenAI only when analyzed; analysis may use a second call for evidence correction.

Analysis creates a draft without changing your active path. Review skill names, change importance, remove irrelevant skills, or add missing skills with exact supporting excerpts. Save reviewed learning path to activate it. A new draft leaves the previous reviewed target active until saved. Use role defaults deactivates the target without deleting learning history or changing module levels. Job descriptions and reviews remain local in the ignored database.

Modules shows available, planned and unmapped matches. Mapping uses curated aliases rather than an LLM inventing module identifiers. Required skills rank before unspecified and preferred skills; recorded weak areas raise priority within each importance group. Suggested prerequisites appear separately from extracted requirements. These are learning priorities, not hiring eligibility or a job-fit score. Broad skills can map to an entire module; available starter lessons do not imply comprehensive coverage.

The additive `job_targets` table stores description, review state, extracted skills, model identifier and active selection. New endpoints are `GET /api/v1/jobs/current`, `POST /api/v1/jobs/analyze`, `PUT /api/v1/jobs/{id}/review`, and `POST /api/v1/jobs/clear`. Active recommendations are returned by `/api/v1/curriculum` and the dashboard. Live verification uses a fictional description and a temporary database; automated tests use an injected extractor.

Job-description-driven interview question filtering, broader content coverage, feedback-quality benchmarking and sourced technology updates remain future work.


## Feedback quality and learner flags

Accepted feedback now offers Flag this feedback. Choose a reason and optionally describe what was missed. A local `feedback_flags` record preserves the original question, answer, feedback and evaluator model. Repeated saves update one report per attempt. Flagging never changes scores, weak areas or review dates and does not send a message to a human reviewer. Recorded flags appear in Your progress and remain editable from the assessed answer.

Endpoints are `GET /api/v1/feedback/flags` and GET/PUT `/api/v1/practice/{id}/flag`. New accepted assessments record evaluator prompt and rubric versions. Existing attempts retain their original results.

The development evaluation harness and baseline/refined reports are in `evals/`. It contains 20 synthetic answer cases, evaluated twice per run. The refined evaluator matched all reference judgments in that small run, compared with 69 of 80 criterion judgments at baseline. These are project-authored development labels, not independent human-reviewed or held-out accuracy results. See `evals/README.md` for definitions, limitations and the review workflow.
# Shared role curriculum

Modules now includes five role tracks, the full supplied roadmap and four starting levels, including Foundational. Set a subject level and optionally override individual topics. Existing learning history is preserved. New roadmap entries and project ladders are marked planned until their lessons and specifications are authored. See [the shared curriculum model and migration notes](docs/shared-curriculum.md).

The first complete submodule is **Python → Variables and data types**, available at Beginner, Foundational, Intermediate and Advanced. It includes local runnable examples, exercises, mini-project rubrics, official reading links, and 16 concept/applied tasks. Submitted code receives feedback as text; the app does not execute it. Earlier lessons and progress remain available.
