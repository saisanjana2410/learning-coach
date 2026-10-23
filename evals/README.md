# Feedback evaluation

This is a development regression set with 20 project-authored reference answers across four questions. Expected judgments were checked against the question rubrics during implementation. **Independent human review is pending.** This is not a held-out benchmark and its agreement metrics are not a general accuracy estimate.

## Initial comparison

Both runs use the same 20 cases with two repetitions, using the configured `gpt-4.1-mini` model alias. Each question has a correct answer, an equivalent paraphrase, an incomplete answer, a clearly incorrect answer, and an uncertain answer.

| Measure | Baseline rubric v2 | Refined rubric v3 |
| --- | --- | --- |
| Valid evaluation outputs | 37 of 40 | 40 of 40 |
| Criterion agreement with reference labels | 69 of 80 | 80 of 80 |
| Score agreement | 33 of 40 | 40 of 40 |
| Repeat consistency | 16 of 20 cases | 20 of 20 cases |
| Equivalent answer consistency | 8 of 8 pairs | 8 of 8 pairs |

Baseline problems included penalizing concise correct answers for lacking unnecessary detail, confusing uncertainty with an incorrect answer, and three failed validations. The refined evaluator adds explicit criterion descriptions for these four questions, independent criterion grading rules, precedence for fully uncertain responses, and one bounded validation correction. Existing learner scores are not retroactively changed.

The same cases informed the refinement and its evaluation, so improved agreement is a development check, not independent validation. The sample omits advanced modules, most coding scenarios, and spoken interviews. A wider human-reviewed held-out set is needed before making claims about grading reliability. Two repeated samples provide only a limited consistency check. Evidence validation checks literal excerpts, not whether the quoted evidence logically supports every judgment.

The JSON reports retain per-case judgments, expected outcomes, failures, question snapshots, prompt versions, dataset hashes, model alias, and latency. Counts refer to evaluation attempts; provider API request totals and token costs were not recorded. Rubric v3 can make an additional correction request after invalid output. API aliases and sampling behavior may change results in future runs.

## Run again

From the project root:

```powershell
.\.venv\Scripts\python evals/run_feedback_eval.py --repetitions 2 --workers 2 --output evals/reports/new_run.json
```

This uses your backend OpenAI key and incurs API usage. It loads only synthetic fixture answers and does not import the application or open its database. The runner checkpoints results after each evaluation and records incomplete runs as running rather than claiming completion.

## Review and extend the labels

1. Have an independent reviewer read each question, reference explanation and criterion description without seeing model output.
2. Record their judgments, identity and review date only after an actual review, and resolve disagreements explicitly.
3. Add new held-out answers before further prompt tuning, including realistic mistakes, mixed correct and incorrect reasoning, and interview clarity cases.
4. Keep development and held-out sets separate, version label changes, and rerun both old and new cases.

`feedback_cases.json` deliberately states that independent review is pending. Do not describe these labels as expert-reviewed until that work is complete.
