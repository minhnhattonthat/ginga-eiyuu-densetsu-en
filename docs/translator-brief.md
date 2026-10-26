# Translator brief - Ginga Eiyuu Densetsu (SNES, Tokuma Shoten 1992)

You translate part of the Japanese script of Legend of the Galactic Heroes, a fleet-battle strategy game that retells
the novels from Astarte to the Baalat Treaty (Yang Wen-li of the Alliance vs Reinhard von Lohengramm of the Empire).
Work only on the batches named in your dispatch, one at a time in the order given, each to a passing check before the
next. Do all translation yourself; do not dispatch subagents.

## Read first
1. `docs/style-reference.md` - voices, approved pairs, layout rules. Match this voice.
2. `build/terms_<batch>.txt` - binding glossary rows for this batch (full table and rulings in `glossary.md`: read its
   Rulings and Style rules sections once).
3. `docs/synopsis.md` - plot order and who is who. Don't give a reveal away early.

## Input: `work/tl/<batch>.tsv`
`id<TAB>speaker<TAB>form<TAB>limit<TAB>Japanese`. form: menu | choice | dlg | narration | name | fragment. limit is the
box's line width in pixels: the build wraps your text to it, so the limit is per line, never per message (boxes
scroll; length is free). ` / ` marks where the JP broke lines: mostly just the original wrap, so ignore it unless it
carries meaning (see Layout). Lines are in story order: use neighbours for context.

Variables: `{sub0:00}` ship name, `{sub0:01}` officer name, `{sub0:02}` rank, `{sub0:03}` a number (ship count),
`{sub0:05}` side ("Alliance" / "Empire"). Fixed fragments, already translated (write around them):
`{sub0:06}` Oberstein, `{sub0:07}` Frederica, `{sub0:08}` Reinhard, `{sub0:09}` Heinessen, `{sub0:0A}` Kircheis,
`{sub0:0B}` the Alliance fleet totals, `{sub0:0C}` the Imperial fleet totals, `{sub0:0D}` "Currently, (an opening
quote mark plus "Currently,": the line that follows continues the sentence, and the message closes the quote),
`{sub0:12}` Lohengramm. A speaker given as `{sub0:08}「` is Reinhard speaking: write `{sub0:08}: "..."`.

## Output: `work/tl/<batch>.out.tsv`, written with your file-write tool (not a shell heredoc)
`id<TAB>English`, every input id exactly once, same order. Plain ASCII: straight quotes, `...`, `--`; no tabs inside
the English, no Japanese or fullwidth characters, no `\uXXXX`, no `\n`.

## Layout
- Running prose; the build wraps it. Write ` / ` (space, slash, space) only where a break must fall: a speaker name
  the JP puts on its own line (`Attenborough / "Our total..."`), a blank-line pause the JP has (`{nl}{nl}` shows as
  ` /  / `: write ` / / `), the `{yesno}` line, list rows. `ON/OFF` (no spaces) is not a break.
- Keep every control code exactly, in the same order and position relative to the text: `{speed:..}` at the start,
  `{wait}` / `{end}` at the end, `{yesno}` on its own line. The check compares them (line breaks excepted).
- Dry run a line: `python -X utf8 tools/wrap.py "<text>" --px 160` prints each wrapped line and its width.

## Validate
Run `python -X utf8 tools/batches.py check <batch>` from the repo root and fix every reported id until it prints OK.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese doesn't
  state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Names and terms exactly as in the glossary (Yang, Reinhard, Kircheis, Schonkopf, Iserlohn Fortress, Rosen Ritter,
  Phezzan, ranks: Commodore, Rear Admiral...). Never abbreviate to fit: the line limit is per line, so it never forces
  a cut. Report a real problem as `LONG: id`.
- Honorifics (D1): 様 after a name -> `-sama` ("Reinhard-sama"). 閣下 -> "Your Excellency". Rank + name: Western order
  ("Commodore Yang", "{sub0:02} {sub0:01}"). Speaker prefix `Name: "..."`.
- Punctuation: 「」 -> "...", 『』 -> '...', … -> `...`, ！？ -> `?!`. Numbers in digits with commas: ２万隻 = 20,000
  ships, １万５千隻 = 15,000 ships. Dates: 宇宙暦７９６年 -> S.E. 796, 帝国暦４８７年 -> I.C. 487.
- Placeholders: a possessive is fine ("{sub0:08}'s fleet": every value is a name); no ordinal glued to a number
  variable ("{sub0:03}th"), no a/an right before a variable.
- Menus: short imperative or question, consistent across the set ("Select ...", "Which ... will you ...?",
  "... Are you sure?").

## Consistency
Never edit `glossary.md`. For a recurring name or term not in it, pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note`.
