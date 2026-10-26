# Ginga Eiyuu Densetsu / Legend of the Galactic Heroes (SNES, Tokuma Shoten 1992) English translation

Skill: translate-retro-game; `python tools/skill.py` prints its folder. Read its SKILL.md before ROM, text or QA work. `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py`  -> build/logh_en.sfc (checks the dump against `rom.sha1` first)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/logh_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/logh_en.sfc --out work/qa/warp1 --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 22000 --sheet` (scenes: `tools/debug/scenes.lua`, facts `docs/re/debug.md`; never ask the user to play to a scene)
- States:   `python -X utf8 tools/debug/regen.py [SCENE..]` (every scene from a cold boot -> `work/states/<scene>.mss` + `work/qa/warp/proof*.png`; rerun after code/font/gfx changes)
- Tour:     `python -X utf8 tools/tour.py [SCENE..]` (phase-8 QA: every state -> a shot per complete box -> `work/qa/tour/<scene>/sheet*.png`; JP side: see its docstring) then `qa_gate.py init|todo|check work/qa/manifest.tsv ...`, visual-qa agents per `docs/visual-qa-brief.md`
- Events:   `python -X utf8 tools/events.py [--event N [--dump]] [--unreached]` (event scripts -> message ids)
- Marker:   `python -X utf8 tools/build.py --marker` (every string shows `[id]`); `--qa ID=TEXT` overrides one string
- Widths:   `python -X utf8 tools/widthgate.py` (ruler + torture line per box variant -> work/qa/width/*.png); `tools/boxes.py` (message -> box, script/boxes.json)
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Ginga Eiyuu Densetsu (Japan).sfc` (LoROM 1 MB, no header; gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1, https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip; gitignored; settings in `tools/emu-config/`). Savestates: `work/states/`.
- Engine: `asm/engine.asm` (VWF, far text, name slots; facts `docs/re/engine.md`), assembled by asar 1.91 in `tools/asar/` (committed with its licences; https://github.com/RPGHacker/asar/releases/tag/v1.91). Font: `tools/font.py`.
- Text: `script/` (JSON). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Never run `gh release create` or change repo visibility; a run ends at a built, verified release zip.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
