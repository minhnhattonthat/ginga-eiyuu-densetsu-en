# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| fonts/ark-pixel-12px-proportional-latin.bdf | Ark Pixel Font by TakWolf, https://github.com/TakWolf/ark-pixel-font release 2026.10.25 (`ark-pixel-font-12px-proportional-bdf`) | SIL OFL 1.1 (`fonts/OFL-ark-pixel.txt`) | yes (OFL allows embedding; ship OFL text with the patch) | dialogue VWF (tools/font.py -> asm/engine.asm) | trimmed to printable ASCII; space advance 6 -> 4 px in tools/font.py |
