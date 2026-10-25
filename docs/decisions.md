# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-26 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western order (given name first). Owner's standing answer for one-shot runs. |
| D2 | 2026-10-26 | Romanization source for names | official, earlier patch, Hepburn | Official English names where they exist (Haikasoru/VIZ novel translation, then the official anime release), else an earlier fan patch (none found), else Hepburn without macrons. |
| D3 | 2026-10-26 | Credits | stay Japanese, translate | English. |
| D4 | 2026-10-26 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default); abbreviate only as a flagged last resort. |
| D5 | 2026-10-26 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); keep the Japanese logo only if it has no official English version. |
| D6 | 2026-10-26 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through every checkpoint; phase end = status update, commit, push to main. Never `gh release create`, never change visibility. |
| D7 | 2026-10-26 | Existing saves / savestates | user-provided, none | None provided; build the debug tool as usual. |
