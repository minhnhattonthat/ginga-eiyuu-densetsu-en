# Ginga Eiyuu Densetsu English translation

Unofficial English fan translation of **Ginga Eiyuu Densetsu** (Super Famicom, Tokuma Shoten, 1992): the source text and tools
that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue / story (all three scenarios, battle cut-ins) | Translated |
| Names, ranks, ship types, command labels | Translated |
| Battle banners and scenario title bars | Translated |
| Title screen (logo, copyright, buttons) | Translated |
| Staff credits | Already in English/German in the original |

Known issues: none known; [report one](../../issues/new/choose).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/ginga-eiyuu-densetsu-en
cd ginga-eiyuu-densetsu-en
# copy your dump to: rom/Ginga Eiyuu Densetsu (Japan).sfc
#   (1,048,576 bytes, SHA-1 b90cc0f0cd63859bea96f0c3eb109e3a9db88e5d; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/logh_en.sfc
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Tokuma Shoten's and is included only so
the translation can be checked against it. Ginga Eiyuu Densetsu is (c) Tokuma Shoten; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
