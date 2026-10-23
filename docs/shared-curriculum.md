# Shared curriculum: first migration

The catalog supports AI Engineer, React Frontend Developer, Python Developer, GenAI Engineer and MERN Full Stack Developer. The supplied source is retained in `backend/app/catalog/role_tracks.txt`: 60 role sections, 300 original topic entries and 20 proposed projects. Compound entries can reference several canonical topics; repeated entries share an identity. Existing lesson and question IDs are preserved.

## Learner flow

1. Create a learning profile, then select a role track in Modules. A reviewed job description continues to take priority over the role template.
2. Read the role's 12-section roadmap and proposed project ladder.
3. Select Beginner, Foundational, Intermediate or Advanced for a subject. Optionally override an individual topic. Resetting a topic to “Use subject level” restores inheritance.
4. Open an available lesson or start continuous conceptual/applied practice inside its submodule. Existing question-specific help, feedback, revision dates and summaries continue to work.
5. Role interviews snapshot effective topic levels at session start. Preference changes apply to future sessions, leaving historical evidence and active difficulty intact.

A starting level is self-reported preference, not demonstrated mastery. Foundational is a distinct level; it is not silently replaced by Beginner. There are currently no Foundational lesson packs. The existing starter packs remain available at their original three levels. Planned subjects and project specifications cannot be started.

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
