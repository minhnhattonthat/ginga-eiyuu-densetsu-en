# Translation reviewer brief - Ginga Eiyuu Densetsu (SNES 1992)

You review one batch of a JP->English fan translation of Legend of the Galactic Heroes. Read-only: no edits, no git,
no subagents. Mechanical validity (ids, control codes, ASCII, line width, glossary spellings) is already enforced by
`tools/batches.py check` - judge translation quality. Return the report as your final message: subagents cannot
write files, so the controller saves it.

## Inputs (paths in your dispatch)
- Pairs file: every translated entry as `>> id | JP` / `EN:` in story order, with 2 context lines either side. Read
  ALL of it. JP ` / ` = the original line wrap; EN ` / ` = a hard break; `{sub0:NN}` variables are listed in
  `docs/translator-brief.md` (Input section).
- `glossary.md` (rulings at the top), `docs/style-reference.md`, `docs/synopsis.md`, the translator's report.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning, wrong numbers (万 =
  10,000). Quote the JP and say what it means.
- Consistency: glossary names/terms exactly (a one-letter slip is what players notice); ranks; voice per the style
  reference (Reinhard curt and proud, Kircheis "Reinhard-sama", Yang wry and polite, narration history-book).
- Things players caught that reviewers missed: jokes/wordplay losing their punch; an ordinal after a variable
  ("1th"); abbreviated names or terms; stock phrases that read awkwardly in English; a variable sentence that reads
  wrong for one of its values (side = "Alliance"/"Empire", any rank or officer name).
- Naturalness: would a reader stumble? Register: military space opera, period-drama dignity.
- Plot: no reveal given away early (synopsis), lines consistent with what comes later.

## Report
### Issues
#### Critical (meaning reversed, broken placeholder grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Approved | Needs fixes - one sentence why.
