# Tech updates

The first version is a manually refreshed digest for the current AI/ML learning focus. It checks six primary-source feeds: Python Insider, scikit-learn releases, MLflow releases, PyTorch Blog, Hugging Face Transformers releases and OpenAI News. The checked-in registry fixes allowed feed hosts and repository paths; the client and model cannot provide arbitrary fetch URLs.

## User flow and API cost

Opening Tech updates reads the local cache only. Refresh updates checks the feeds, selects up to five qualifying recent items and saves the digest. The default is source excerpts plus curated learning suggestions: no model call. The optional AI summaries checkbox enables a single bounded structured-summary request when a new summary is needed. Reopening a saved digest and saving/removing items do not call the model. Learner drafts, job descriptions, profile details and practice history are not sent to the summarizer.

Source checks are limited to once per minute. A digest fingerprint includes the selected source records; unchanged AI summaries are reused rather than regenerated. This is manual refresh, not a scheduled background job. When the digest is not checked on the current profile-local day, or sources failed, the UI recommends checking again.

## What qualifies

Entries must have a parseable source timestamp/date, a verified HTTPS source link and a source date within the last 30 days and not in the future. Missing or unqualified timestamp timezones are not guessed. RSS publication dates and Atom update-only dates are distinguished: the latter is labeled Source updated, not Published. Timestamp days are displayed in the learner's profile timezone, named on each card; the original normalized source timestamp remains available in the time element tooltip. A date-only source date is retained as a source calendar date.

Selection uses transparent keyword/version signals for security, releases, breaking changes, training, inference, evaluation and related engineering topics, with penalties for previews and corporate/community announcements. It takes at most one item per source and five total. It does not fill a quota, assert exhaustive coverage, or claim every selected item was published today. Readers can inspect every official source's last-check status.

Only metadata and text excerpts are retained. HTML/script content is stripped, XML entities/DOCTYPE are rejected, feed response sizes and timeouts are bounded, redirects are restricted to the configured official hosts, and unrelated GitHub repository links are rejected. This version reads at most the first 100 entries per feed.

## Summaries and provenance

Source titles, URLs and dates are never model-generated. Optional AI output supplies only the summary, relevance explanation, suggested learning action and an exact supporting excerpt, tied to an existing article ID. Validation requires exactly the expected IDs and evidence present in the corresponding source text. Invalid/failed AI output falls back to source excerpts and reports the failure. Evidence matching and JSON validation do not establish semantic accuracy; AI cards are labeled and link to the original source.

Related lesson links use current topic starting preferences and authored lesson availability. The label Review related foundations does not claim that a static course lesson already covers a new release. Future topics lead to their coming-soon catalog outline. Updates do not award mastery or change practice scores.

## Persistence and recovery

`tech_digests` stores the latest successful digest, fingerprint, summary mode and optional prompt version. `tech_update_checks` independently records the latest check time, source coverage and notice. `saved_tech_updates` stores immutable saved-card snapshots and saved timestamps. Startup adds these tables; learner history is untouched.

A completely failed check retains the previous digest and records failure coverage. A partially failed check can show qualifying items from available sources, explicitly labeled partial. A partial check with no items preserves an existing digest. A successful complete check with no qualifying items saves an honest empty digest. Saved snapshots remain available when the current digest changes and may be older than the news window.

Endpoints:

- `GET /api/v1/tech-updates`: cached digest, source/check status and saved items; no network fetch.
- `POST /api/v1/tech-updates/refresh` with `use_ai: false` by default.
- `PUT /api/v1/tech-updates/{article_id}/save` with `saved: true` or `false`.

Tests use offline RSS/Atom fixtures and injected fetchers/summarizers/clocks. They cover date filtering, URL/source constraints, excerpts, caching, opt-in AI, source-evidence validation, saved snapshot persistence, feed failures, timezone behavior and empty/no-filler selection. Live verification is performed with AI summaries disabled.
