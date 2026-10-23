# Shared curriculum: first migration

## Current release scope

The active release is Python for ML, MLOps basics and a guided delivery-time prediction project. Other modules remain visible with a Coming soon label; earlier starter lessons remain available rather than removing existing learning paths or evidence. The full supplied role outlines remain accessible in a collapsed roadmap.

Three focused submodules each have four authored levels and four assessment tasks per level: two conceptual questions and two practical tasks. This adds 12 lessons and 48 tasks. The additive `focused-ml-path-v1` migration stores the new topics, content versions and skill links without rewriting learner history. A starting preference still does not claim mastery.

The downloadable project kit contains local synthetic-data training, a baseline comparison, train/validation/test selection, a saved pipeline and versioned manifest, a validated FastAPI endpoint and optional local MLflow logging. Training and serving require no external API calls. Learner code is not executed by Learning Coach; applied submissions receive text-based rubric feedback. `GET /api/v1/projects/delivery-time/starter.zip` streams only the checked-in starter files, excluding model artifacts, databases and credentials.

The experimental all-topic generator has not been integrated or activated. Lesson reading and local project runs make no OpenAI calls; tutor chats and assessment feedback retain their existing API use.

### Saved guided-project work

The Guided project view adds a workspace per learner/project/level, persisted in `project_workspaces`. `project_milestone_drafts` stores draft text with an optimistic version to reject stale-tab overwrites. `project_milestone_submissions` links an idempotent client submission ID to an immutable existing `practice_attempts` record. Tables are added on startup without modifying existing learner records or accepted evidence.

The six milestone definitions supply level-specific framing, visible rubrics and advanced release checks. Each links to an existing Python for ML, ML project or MLOps lesson at the workspace's frozen level. Saved feedback uses those existing skill/topic identities, so gaps participate in the established applied-practice revision logic. Missing/uncertain evidence does not complete a milestone. Only a 100% score across all rubric criteria in the latest accepted submission produces “Requirements met”; there is no independent mastery or code-execution claim.

Draft save and workspace navigation do not call OpenAI. Feedback requests do. Failed evaluations preserve the submitted answer for exact retry; cancelling a pending evaluation retains its history. Repeating an already accepted request is idempotent, and submitting identical accepted work under a new ID is rejected before making a model call. Project pending work is excluded from ordinary practice's pending-question selection so it is not accidentally adopted as a learning-session question.

Endpoints under `/api/v1/projects/delivery-time`:

- `GET` returns the most recently used workspace and resume point, or available levels before the first start.
- `POST /start` opens or resumes the requested level's separate workspace.
- `GET /workspaces/{workspace_id}` retrieves a specific workspace without switching to another level's most recently used work.
- `PUT /{workspace_id}/milestones/{milestone_id}/draft` saves text with its expected draft version.
- `POST /{workspace_id}/milestones/{milestone_id}/submit` requests feedback with a stable submission ID and answer.

Feedback flags, question-specific discussions and cancelling pending evaluations reuse the existing practice endpoints. Drafts are saved explicitly or when selecting a different milestone; the UI identifies unsaved changes before leaving or switching levels.

The catalog supports AI Engineer, React Frontend Developer, Python Developer, GenAI Engineer and MERN Full Stack Developer. The supplied source is retained in `backend/app/catalog/role_tracks.txt`: 60 role sections, 300 original topic entries and 20 proposed projects. Compound entries can reference several canonical topics; repeated entries share an identity. Existing lesson and question IDs are preserved.

## Learner flow

1. Create a learning profile, then select a role track in Modules. A reviewed job description continues to take priority over the role template.
2. Read the role's 12-section roadmap and proposed project ladder.
3. Select Beginner, Foundational, Intermediate or Advanced for a subject. Optionally override an individual topic. Resetting a topic to “Use subject level” restores inheritance.
4. Open an available lesson or start continuous conceptual/applied practice inside its submodule. Existing question-specific help, feedback, revision dates and summaries continue to work.
5. Role interviews snapshot effective topic levels at session start. Preference changes apply to future sessions, leaving historical evidence and active difficulty intact.

A starting level is self-reported preference, not demonstrated mastery. Foundational is a distinct level; it is not silently replaced by Beginner. Variables and data types now has a complete lesson pack at all four levels, including Foundational. The earlier starter packs remain available at their original three levels. Planned subjects and project specifications cannot be started.

## Data model and ownership

| Concept | Current storage |
| --- | --- |
| Role | `catalog_roles`: stable ID, title and versioned role payload, including sections and original source-topic mappings |
| Module | `catalog_modules`: stable ID and payload containing title, objectives, order and topic references |
| Topic | `catalog_topics`: stable ID, module foreign key and payload containing prerequisites, supported starting levels, objectives and availability; estimated hours remain unset |
| RoleTopic | `role_topics`: role/topic composite key, importance, order, role context and source references |
| Skill / TopicSkill | `catalog_skills`, `topic_skills`: explicit identities; identical labels in different topics do not merge assessment evidence |
| Lesson / Assessment | `content_versions`: immutable kind/ID/version identity and snapshot payload; legacy question-only topics remain valid |
| AssessmentAttempt | Existing `practice_attempts`: exact question snapshot, submitted answer, criterion feedback, score, model and timestamps |
| Project | `catalog_projects`: role, level and planned payload. Titles are supplied; requirements and rubrics are not yet authored |
| Learner starting preferences | Existing profile and `module_preferences`, plus `topic_preferences` keyed by learner and topic |
| LearningProgress / LearnerSkill | Derived from accepted attempts through `/progress`, grouped by topic, skill, mode and level. Evidence and revision dates remain authoritative; no competing mutable mastery table is introduced |
| Session snapshot | Existing `run_preferences`: module levels and effective topic levels captured at start |
| Migration | `schema_migrations`: applied catalog version and timestamp |

This is a catalog migration, not a database authoring interface. The curated Python catalog supplies runtime definitions; normalized tables retain the migration snapshot. Future catalog changes require an explicit new seed/migration version. Existing marker versions are never silently reseeded.

## Lesson contract

New complete lessons should provide objective/prerequisites; what and why; explanation plus example; runnable code where appropriate; guided exercise; independent challenge; assessment and feedback; mini-project task and mastery rubric; further reading and next prerequisite-linked topic.

Existing starter lessons keep their content unchanged. Their versioned definitions identify available concept/example sections and leave unauthored exercises, runnable-code artifacts, mini-projects and reading empty. Assessment snapshots retain question sets and criterion rubrics; passing thresholds remain unset rather than implying a new mastery policy. This milestone does not execute learner code.

## Migration and recovery

Startup adds tables and seeds `shared-curriculum-v1` transactionally once. No existing learner, preference, conversation, question, feedback, run, job target or progress record is rewritten. For the existing local SQLite database, startup first creates an ignored backup at `backend/backups/before-shared-curriculum-v1.db`. Test databases do not create production backups.

New preference endpoints:

- `PUT /api/v1/curriculum/role` with `role_id`.
- `PUT /api/v1/curriculum/topics/{topic_id}/level` with `level`, or `null` to inherit.
- Existing `PUT /api/v1/curriculum/{module_id}/level` supports all four levels.

`GET /api/v1/curriculum` includes five roles, the selected track, source sections, planned projects and each topic's effective level, inheritance source and actual available lesson levels. Missing content stays visibly planned and cannot create an empty practice session.

## Python variables and data types release

The `python-basics` submodule provides four authored lessons: names and everyday types; input conversion and missing values; runtime type contracts; numeric representation and rounding. Each lesson includes its objective and prerequisites, explanation, worked example, runnable Python sample with expected output, guided exercise, independent challenge, mini-project task and visible assessment criteria, official reading links and suggested next topics.

Concept practice selects concept checks and transfer questions. Applied practice selects a mini-project or independent challenge. There are two tasks per mode per level (16 tasks total). Submitted code is evaluated as text with criterion-based feedback and the existing evidence/revision logic; learner code is never executed by the service. Reading a lesson does not automatically award mastery.

The content migration `python-basics-lessons-v2` adds versioned lesson/question snapshots and topic-skill links, then publishes availability for `python-basics`. It preserves prior content snapshots and learner evidence. The supplied role project ladders remain planned; these small lesson exercises are separate from those role projects.

Reading sources: [Python tutorial](https://docs.python.org/3/tutorial/introduction.html), [built-in types](https://docs.python.org/3/library/stdtypes.html), and [Decimal](https://docs.python.org/3/library/decimal.html).
