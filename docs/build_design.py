from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent
d = Document()
s = d.sections[0]
s.page_width, s.page_height = Inches(8.5), Inches(11)
s.top_margin = s.bottom_margin = Inches(.7)
s.left_margin = s.right_margin = Inches(.8)
for name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2']:
    style = d.styles[name]
    style.font.name = 'Calibri'
    style.font.color.rgb = RGBColor(0, 0, 0)
    for border in style.element.xpath('./w:pPr/w:pBdr'):
        border.getparent().remove(border)
d.styles['Normal'].font.size = Pt(10.5)
d.styles['Normal'].paragraph_format.space_after = Pt(7)
d.styles['Heading 1'].font.size = Pt(19)
d.styles['Heading 2'].font.size = Pt(12)

def p(text):
    d.add_paragraph(text)

def h(text):
    d.add_heading(text, 2)

def page(title):
    d.add_page_break()
    d.add_heading(title, 1)

def bullets(items):
    for item in items:
        d.add_paragraph(item, 'List Bullet')

def table(headers, rows, widths):
    t = d.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for col, width in zip(t.columns, widths):
        col.width = Inches(width)
    for i, value in enumerate(headers):
        t.rows[0].cells[i].text = value
    for values in rows:
        cells = t.add_row().cells
        for i, value in enumerate(values):
            cells[i].text = str(value)
    for ri, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        if ri == 0:
            trpr.append(OxmlElement('w:tblHeader'))
        for ci, cell in enumerate(row.cells):
            cell.width = Inches(widths[ci])
            pr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for edge in ['top', 'left', 'bottom', 'right']:
                e = OxmlElement('w:' + edge)
                for key, value in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
                    e.set(qn('w:' + key), value)
                borders.append(e)
            pr.append(borders)
            shading = OxmlElement('w:shd')
            shading.set(qn('w:fill'), 'DCE6F1' if ri == 0 else ('F3F6F8' if ri % 2 == 0 else 'FFFFFF'))
            pr.append(shading)
            margins = OxmlElement('w:tcMar')
            for edge in ['top', 'bottom', 'left', 'right']:
                e = OxmlElement('w:' + edge)
                e.set(qn('w:w'), '70')
                e.set(qn('w:type'), 'dxa')
                margins.append(e)
            pr.append(margins)
            for para in cell.paragraphs:
                para.paragraph_format.space_before = Pt(3)
                para.paragraph_format.space_after = Pt(3)
                for run in para.runs:
                    run.font.size = Pt(9)
                    run.bold = ri == 0
    d.add_paragraph()

# Each section is deliberately page-sized for a readable implementation reference.
d.add_heading('Learning Coach', 0)
d.add_paragraph('Architecture and implementation reference', 'Subtitle')
p('Version 2.0 | October 23 2026 | Current local MVP')
p('A personal learning and interview preparation system connecting assessment, teaching, practice, evidence-based feedback, revision, and progression. This document replaces the original design baseline and describes implemented behavior, with future work identified explicitly.')
h('Current product focus')
p('Python for ML, MLOps, and a guided ML project form the active path. Four experience levels tailor lessons and task difficulty. Other career-track modules remain visible as Coming soon. Saved practice and interview results feed shared weak-area and revision views.')
h('Architecture principle')
p('Use a bounded LangChain tutor for teaching and separate structured model calls for evaluation and extraction. Keep assessed-question selection, scoring, persistence, retries, and revision scheduling in deterministic application services.')
table(['Section', 'Coverage'], [
('1', 'Scope and content coverage'), ('2', 'Architecture and technology'),
('3', 'User flows and frontend'), ('4', 'AI tools and execution boundaries'),
('5', 'Persistence and data relationships'), ('6', 'Assessment and revision'),
('7', 'Guided ML project'), ('8', 'Technology updates'),
('9', 'Operations and verification'), ('10', 'Limitations and delivery priorities')], [.7, 6.2])
p('Audience: developer, project owner, and technical reviewer. This is a single-learner localhost application, not a deployed multiuser learning platform.')

page('1 Scope and content coverage')
h('Problem and outcome')
p('Learners often separate explanations, interview questions, projects, and revision across tools. Learning Coach keeps these activities connected through durable answer evidence, targeted clarification, and a visible revision queue. It does not claim to certify job readiness.')
table(['Area', 'Current implementation'], [
('Profile and targeting', 'Role, level, study preferences and timezone; reviewed job descriptions influence topic recommendations.'),
('Learning', 'Authored lessons, persistent tutor discussions, conceptual and applied practice within submodules.'),
('Interview', 'Continuous role-filtered question runs and summaries using the available curated question bank.'),
('Feedback and revision', 'Rubric evidence, question-specific help, local feedback flags, weak areas and due reviews.'),
('Projects', 'Downloadable ML starter, six milestones, draft saves and assessed submission snapshots.'),
('Updates', 'Manual official-source digest, cached reading, optional AI summaries and bookmarks.')], [1.35, 5.55])
h('Catalog versus authored content')
p('The shared catalog contains 5 roles, 26 modules, and 271 canonical topics representing 300 supplied role-topic entries across 60 source sections. Reuse avoids duplicating common Python, API, testing, security, and deployment topics. A listed topic is not necessarily a complete lesson.')
p('There are 30 authored lessons and 102 bank questions. The focused path contributes 12 lessons and 48 tasks across Python for ML, MLOps basics, and the ML project at four levels. Python variables and types contributes 4 lessons and 16 questions. Retained starter material contributes 14 lessons and 38 questions. Project milestone rubrics are separate from that count.')
h('Content structure')
p('Role → recommended reusable modules/topics → submodule lessons and conceptual/applied tasks. Prerequisite links and reviewed job requirements inform navigation. The intended lesson template includes objectives, prerequisites, explanations, worked examples, code where appropriate, exercises, feedback, and next topics. Broader full-template coverage and the 20 role/level project-ladder titles remain planned.')

page('2 Architecture and technology')
table(['Layer', 'Technology', 'Responsibility'], [
('Interface', 'React 19, Vite 7, CSS', 'Views, forms, persisted workflows, Markdown and KaTeX rendering.'),
('API', 'FastAPI and Pydantic', 'Request contracts, validation and service coordination.'),
('AI', 'LangChain and ChatOpenAI', 'Bounded tutor and separate structured model operations.'),
('Persistence', 'SQLAlchemy and SQLite', 'Local learner state, snapshots, catalog and caches.'),
('Content', 'Versioned definitions and seeds', 'Reusable catalog, lessons, questions and rubrics.'),
('ML example', 'scikit-learn, joblib, FastAPI', 'Synthetic training workflow and separate prediction service.'),
('Verification', 'pytest, Node tests, Vite build', 'Service behavior, rendering and build checks.')], [1.05, 2.15, 3.7])
h('Request and state paths')
p('React → FastAPI → application services → SQLite. AI actions additionally call the tutor or a structured model service. Tech refresh calls allowlisted feed endpoints. The browser does not hold the OpenAI key or access the database directly.')
p('The tutor exposes read-only lesson and profile tools. The application supplies current lesson and saved weak-area context. Separate services handle question selection, answer evaluation, job extraction, project workflows, and updates. No vector database, multiagent system, or arbitrary code runner is present.')
h('State ownership')
p('SQLite is authoritative for accepted learner records. Model prose cannot change grades, review dates, or workspace state. Structured evaluation is validated before deterministic scoring. Immutable accepted snapshots provide the evidence used by progress views.')
h('Runtime assumptions')
p('Python 3.11+ and Node.js 22.12+. The development setup runs a localhost API on port 8001 and Vite normally on 5173. The configured model default is gpt-4.1-mini. This names the current configuration, not a recommendation about the latest model. Local single-worker locks and SQLite are not a production multiworker concurrency design.')

page('3 User flows and frontend')
table(['View', 'User action and outcome'], [
('Overview', 'See current learning activity and continue available work.'),
('Learning profile', 'Choose role, one of four levels, preferences and timezone.'),
('Job target', 'Paste a description, inspect extracted requirements, review mappings, and activate the target.'),
('Modules', 'Browse available and Coming soon modules; open a submodule lesson and practice.'),
('Role interview', 'Practice across available role topics with a fixed run context.'),
('Guided project', 'Download starter, save milestone drafts, submit evidence and resume work.'),
('Your progress', 'Inspect accepted attempts, weak areas and due reviews.'),
('Tech updates', 'Read cached items, refresh sources, opt into AI summaries, and save articles.')], [1.3, 5.6])
h('Continuous learning')
p('Choose a submodule once → learn and ask the tutor → begin conceptual or applied practice → submit an answer → inspect criterion feedback → ask question-specific follow-ups → continue to another question → end the run and view a summary. There is no fixed session length.')
p('Run preferences freeze the selected level and relevant module/topic context. Interview runs freeze their allowed role topics. Switching profile settings does not silently reinterpret an existing run. The interview question bank is curated, not generated from a pasted job description.')
h('Clarification and learner control')
p('The side discussion receives only the current question, submitted answer, reference material, feedback, and its own conversation. It can explain a misunderstanding without changing the accepted grade. Feedback flags preserve the original snapshot and are stored locally; they are not sent to a human reviewer.')
h('Job target workflow')
p('Structured extraction requires exact source quotations and bounded correction. The learner reviews requirements and importance. Alias mapping labels available, planned, and unmapped topics. An active reviewed target overrides default role ranking while explicit prerequisite relationships remain separate. Clearing the target retains history.')

page('4 AI tools and execution boundaries')
table(['Operation', 'Context and limits'], [
('Tutor', 'LangChain create_agent with get_lesson and get_learning_profile; current lesson and weak-area summaries supplied by the server.'),
('Tutor bounds', 'Recent 16 messages, recursion limit 8, timeout 25 seconds, max retries 0, output limit 900 tokens.'),
('Assessment', 'Stored question/rubric and submitted answer; structured criterion judgments, exact evidence checks, one bounded validation correction.'),
('Question help', 'Only this question, answer, reference, accepted feedback, and discussion history; no broader profile tools.'),
('Job extraction', 'Pasted job description, structured requirements with source quotations, and bounded repair.'),
('Optional news summary', 'Selected source entries only; 40-second timeout, max retries 0, output limit 2600 tokens, source-ID and evidence validation.')], [1.25, 5.65])
h('Agent responsibilities')
p('The tutor can select read-only lesson/profile tool calls and adapt explanations. It cannot select or grade the assessed question through a tool, write progress, execute submitted programs, browse arbitrary websites, or use a hidden collection of history tools. Teaching chat remains distinct from assessment evidence.')
h('Cost boundaries')
p('Tutor messages, evaluation, question help, and job analysis call OpenAI. Browsing authored content, progress, project drafts, or cached updates does not. Default feed refresh uses no model call. Explicitly enabling AI summaries may make one bounded call when a new summary is needed; unchanged fingerprints reuse cached summaries.')
h('Failure and retry behavior')
p('Attempts are persisted before provider calls. A retry must keep the original ID and answer. Accepted evaluation is reused rather than regraded on duplicate submission. Pending failed project submissions remain separate from normal practice. Model errors are visible and retryable; they do not create accepted mastery evidence.')
h('Secrets and privacy')
p('The key stays in backend/.env, which is ignored by Git. AI requests transmit relevant user input and context to the configured provider. Local storage is not an authentication or encryption boundary. Provider usage and cost depend on enabled AI actions; automated tests use injected fixtures.')

page('5 Persistence and data relationships')
p('The current database has 25 tables. Reusable content definitions often live in JSON payload columns; this is not the fully normalized conceptual schema proposed in the original baseline. Learner identity is currently local learner 1.')
table(['Table group', 'Tables and relationships'], [
('Catalog', 'catalog_roles, catalog_modules, catalog_topics, catalog_skills, catalog_projects; role_topics joins roles to topics and topic_skills joins topics to skills.'),
('Profile and preferences', 'learners; module_preferences and topic_preferences; run_preferences stores run-specific choices.'),
('Learning records', 'learning_sessions stores tutor conversation; learning_runs groups practice; practice_attempts stores answers and accepted evaluation evidence.'),
('Help and reporting', 'question_discussions stores question-scoped threads; feedback_flags preserves reported feedback snapshots.'),
('Job targeting', 'job_targets retains extracted/reviewed target snapshots and active selection.'),
('Project work', 'project_workspaces scopes work by learner/project/level; project_milestone_drafts stores versioned drafts; project_milestone_submissions links immutable submissions to practice attempts.'),
('Updates', 'tech_digests stores cached digest snapshots; tech_update_checks records refresh state; saved_tech_updates retains bookmarked snapshots.'),
('Version tracking', 'content_versions and schema_migrations record seed/migration markers.')], [1.3, 5.6])
h('Derived state and snapshots')
p('Weak areas, mastery-like summaries, and due dates are derived from accepted practice_attempts. There is no separate mutable LearnerSkill, LearningProgress, or ReviewItem table. Project submissions use existing applied-attempt feedback so project gaps connect back to course skills.')
p('A workspace has milestone drafts and submission history. Independent level workspaces preserve each level’s work. Optimistic draft versions reject stale writes. Saved news records retain their original article snapshot after digest refreshes.')
h('Evolution and backup')
p('Startup creates missing tables and runs versioned content seeds. Shared-curriculum migration preserves a local ignored backup before migration. Current additive creation and seed markers are not a general schema-alteration migration framework. Proper migrations and cross-process concurrency controls are future deployment work.')

page('6 Assessment and revision')
h('Evaluation pipeline')
p('Load the server-owned question and rubric → persist answer → request structured judgments → validate coverage and answer quotations → allow one bounded correction → calculate score deterministically → accept feedback → derive progress and review recommendations. A rejected or failed model response does not become accepted feedback.')
table(['Judgment or state', 'Meaning'], [
('met', 'The submitted evidence satisfies the criterion.'),
('partial', 'Some required evidence is present but incomplete.'),
('not_met', 'The criterion is not demonstrated by the answer.'),
('insufficient_evidence', 'The evaluator cannot support a reliable judgment; the overall score is absent.'),
('Accepted feedback', 'Stored result reused on retries; help and reports do not mutate it.')], [1.55, 5.35])
h('Weak areas and scheduling')
p('Accepted attempts are grouped by skill, mode, module, submodule, and level. This prevents unrelated levels or activity types from silently overwriting one another. Interview and applied evidence remain visible through shared progress summaries.')
table(['Evidence', 'Current revision interval'], [
('Score below 50', '1 day'), ('Partial performance', '2 days'),
('Fully correct performance', '4 days'),
('Later demonstrated proficiency', '8 days after a correct distinct-question result at least four days later and after the latest recorded gap.')], [3.25, 3.65])
p('These rules are explicit heuristics. A score or a passed rubric is not a validated measure of long-term retention, interview readiness, or real-world execution skill.')
h('Feedback quality evidence')
p('The live evaluation harness contains 20 synthetic development cases. Two repetitions yield 40 evaluated answers and 80 criterion judgments. Rubric v2 matched 69/80 expected judgments; refined v3 matched 80/80 on the same development set. This demonstrates a development regression improvement, not held-out accuracy. Independent expert review and a separate held-out set remain pending. Live evaluation runs consume model tokens.')

page('7 Guided ML project')
h('Starter workflow')
p('The downloadable delivery-time starter contains README.md, requirements.txt, train.py, and serve.py from examples/ml_project. The API packages these fixed files, excluding keys, databases, and generated model artifacts.')
table(['Stage', 'Implemented example'], [
('Data', '120 deterministic synthetic rows, seed 42; distance_km and traffic_index predict delivery minutes.'),
('Split', '72 training, 24 validation and 24 test rows.'),
('Training', 'Pipeline: SimpleImputer → StandardScaler → Ridge. Compare alpha 0.1, 1 and 10 using validation MAE.'),
('Evaluation', 'Evaluate the selected fixed winner and training-mean baseline on held-out test rows; no train-plus-validation refit.'),
('Artifact', 'Joblib pipeline and manifest with feature order/units, metrics, split sizes, selected settings, model version, runtime/package versions and source/artifact hashes.'),
('Serving', 'Separate FastAPI /health and /predict routes. Strict finite numeric inputs, distance 0–100 and traffic 0–1; reject booleans, strings and extra fields.'),
('Tracking extension', 'Optional --track logs to local MLflow after a separate install. No built-in app MLflow server is required.')], [1.05, 5.85])
h('Learning workspace')
p('Six milestones cover data, baseline, training, evaluation, deployment, and monitoring at each of four levels. Save draft explicitly; switching milestones saves the current dirty draft. Save before leaving or switching levels. Resume the last-worked workspace and inspect accepted feedback history.')
p('Submission snapshots are immutable and linked to applied attempts with the related course skill/topic/level. Stable IDs and unchanged answers support safe retries. Duplicate accepted work under a new ID is rejected before another provider call. The latest fully met rubric earns Requirements met.')
h('Interpretation limits')
p('Assessment reviews submitted text rather than executing code. Requirements met is not a certificate or proof of deployment correctness. Synthetic metrics illustrate a reproducible process, not business model performance. Artifact checksums detect mismatch but do not authenticate an untrusted joblib file; load controlled artifacts only.')

page('8 Technology updates')
h('Source and refresh flow')
p('Open cached digest → explicitly refresh → fetch allowlisted official RSS/Atom feeds → validate dates and URLs → curate relevant items → optionally summarize → save digest → bookmark useful entries. GET requests for cached content do not fetch sources or call a model.')
table(['Source', 'Official feed family'], [
('Python', 'Python Insider RSS'), ('scikit-learn', 'GitHub repository release Atom'),
('MLflow', 'GitHub repository release Atom'), ('PyTorch', 'Official blog RSS'),
('Transformers', 'Hugging Face GitHub repository release Atom'), ('OpenAI', 'Official news RSS')], [1.4, 5.5])
h('Ingestion and selection')
p('Consider the last 30 days; reject undated and future entries. Preserve normalized source timestamps and whether the date is published or updated, and display dates in the learner timezone. Each feed is bounded to its first 100 entries, 2 MB, and a 15-second request. HTTPS host/repository path and redirect restrictions, HTML stripping, and XML entity/doctype rejection constrain ingestion.')
p('Deterministic keyword/version rules select up to five items and at most one per source, with penalties for preview and corporate/community announcements. This is a focused digest, not comprehensive reporting. A 60-second manual-refresh limit prevents rapid repeated checks. There is no automatic daily scheduler.')
h('Cache and AI behavior')
p('Excerpts and curated learning actions work without OpenAI. The explicit AI option uses one bounded structured call when needed. The model cannot generate source URLs, titles, or dates. IDs and quoted evidence must match supplied entries; failures fall back to excerpts. Semantic correctness is not guaranteed by these checks.')
p('All-source failures retain cached content. Partial source status remains visible; a partial zero-item result preserves previous content, while a complete successful zero-item refresh saves an empty digest. Fingerprints reuse unchanged summaries. Saved items retain snapshots beyond the current window. Related foundation links respect level and Coming soon availability.')

page('9 Operations and verification')
h('Local setup')
p('Create a virtual environment and install backend/requirements-dev.txt. This includes runtime, tests, and ML-example dependencies. Copy backend/.env.example only if backend/.env is absent, then set OPENAI_API_KEY. Run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8001. In frontend, run npm ci and npm run dev. See README.md for copyable PowerShell commands.')
p('The runtime backend requirements are sufficient for the learning app; the example adds ML dependencies. The older backend lock snapshot does not represent a complete current ML-example environment. Secrets, local databases/backups, artifacts, and render previews are excluded from Git.')
h('API surface')
p('FastAPI serves profile/catalog/lesson data; tutor sessions; practice and interview runs, attempts and progress; question discussions and feedback flags; job targets; project workspaces, drafts and submissions; and cached/refreshed/saved tech updates. Use the running API’s /docs page for exact request schemas rather than assuming design-baseline endpoint names.')
p('The starter download is GET /api/v1/projects/delivery-time/starter.zip. The prediction example runs separately and exposes /health and /predict. It is not the Learning Coach API process.')
h('Verification snapshot')
table(['Check', 'Latest completed result'], [
('Backend suite', '91 tests passed, including persistence, retry/evidence validation, curriculum, projects, and feed/cache failure behavior.'),
('Frontend', 'Production build passed. Vite chunk-size warning above 500 KB remains nonblocking; Markdown rendering also has Node tests.'),
('ML example', 'Offline training and API prediction parity covered; synthetic dataset and held-out evaluation.'),
('Official sources', 'All six live feeds checked successfully; five cached items with AI disabled. No model tokens used for this source check.'),
('Feedback evaluation', 'Synthetic development harness results documented separately; no held-out or expert accuracy claim.')], [1.4, 5.5])
h('Recheck commands')
p('From the root: .\\.venv\\Scripts\\python -m pytest backend/tests -q; node --test frontend/src/CoachMessage.test.js. From frontend: npm run build. Tests inject model fixtures; a separate live evaluation run is a paid provider operation. Results above are the latest implementation checks, not a claim that documentation editing reran every test.')

page('10 Limitations and delivery priorities')
h('Current boundaries')
bullets([
'Local single learner without authentication, production deployment, or multiworker guarantees.',
'Limited authored bank despite a broad reusable catalog; no complete advanced course for every listed track.',
'No automatic diagnostic, readiness certification, learner-code execution, arbitrary web browsing, or scheduled daily news.',
'Job descriptions change reviewed recommendations, not the underlying question bank.',
'Feedback evidence validation and synthetic evaluation do not establish independent grading accuracy or learning gains.',
'Feedback flags are local records; draft saves and learner-visible retry controls remain part of the workflow.'
])
h('Next delivery priorities')
table(['Priority', 'Concrete outcome'], [
('1', 'Record an end-to-end demo and collect real learner feedback across lesson, practice, revision, project and news flows.'),
('2', 'Build an independently reviewed held-out assessment set and report results separately from development cases.'),
('3', 'Deepen authored lessons and practical tasks within the current Python, MLOps and project path.'),
('4', 'Add authentication, formal migrations, deployment controls and concurrency support when moving beyond localhost.'),
('5', 'Expand other catalog modules and project ladders with verified content rather than claiming catalog coverage as course completion.')], [.7, 6.2])
h('Resume framing')
p('Describe a working local learning platform with a tool-assisted LangChain tutor, structured rubric validation, durable attempt history, revision heuristics, an ML workflow example, and cached official-source ingestion. State the development-set evaluation context explicitly. Avoid claims of autonomous end-to-end teaching, production scale, or proven learning improvement.')
h('Repository references')
p('README.md: setup, scope and commands. docs/shared-curriculum.md: catalog and seed behavior. docs/tech-updates.md: feeds and cache rules. examples/ml_project/README.md: training and serving. evals/README.md: feedback evaluation methodology. docs/build_design.py: source for this document.')

footer = s.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Learning Coach  |  ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
d.core_properties.title = 'Learning Coach Architecture and Implementation Reference'
d.core_properties.subject = 'Current local MVP architecture and delivery status'
d.core_properties.author = ''
d.save(ROOT / 'Learning_Agent_Architecture.docx')
print(ROOT / 'Learning_Agent_Architecture.docx')
