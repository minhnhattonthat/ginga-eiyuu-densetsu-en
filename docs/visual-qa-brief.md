# Visual-QA reviewer brief - Ginga Eiyuu Densetsu (SNES) English

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

`$SKILL` = the folder `python tools/skill.py` prints.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- The original ROM's sheets: `work/qa/tour_jp/<scene>/sheet*.png` (same scene names; the page split may differ
  because English text types at a different length), and `glossary.md`.

How the tour was made (`tools/tour.py`): each scene starts from a savestate; a frame is shot when a text box is
complete and waits for a key, then A is pressed; on screens with no text wait (menus, battles, maps) A is pressed
and a frame shot every 300 frames. So pressing A in menus picks commands: odd menu paths are the tour's, not bugs.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that
  (scratch = a path under `work/qa/scratch/`). Each tile is a 256x224 frame (sheets are full size, 4 columns).
- When something looks wrong, open the JP sheets of the same scene. If the original shows the same thing, it is the
  game's own behaviour: `ok`, with a note.

## Judge
An `issue` is any of:
- Japanese still visible (kana/kanji in a text box, a plate or a label);
- text overflowing a box, clipped by a frame, or running off screen;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-word, a one-word last line;
- an empty box where text belongs (the JP sheet has text there);
- a name that differs from `glossary.md`;
- English that is plainly wrong for the scene (a speaker's portrait vs the name before the colon).

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- black or dark frames between scenes, a scene still loading;
- anything identical in the original's sheet;
- narration that pages: a box ending mid-sentence and the next tile continuing it (the game scrolls story text, one
  key press per page, as the JP does);
- the small round blink cursor at a box's bottom right (the wait-for-key mark);
- names and numbers in romaji/digits in battle panels (`Legrange`, `VICE ADMIRAL`, `20000`) are the English build's;
- after a command is picked (Front, Fleet...), the message box stays empty for ~3 s before the next prompt ("Which
  area will you attack?"): known, logged in docs/status.md;
- the 3x5 all-caps rank and ship-type plates (`VICE ADMIRAL`) are deliberate (small sheet tiles).

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile (row, column), which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
