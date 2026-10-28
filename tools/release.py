"""Build and verify a release: build -> check -> smoke -> jp_left -> qa_gate -> patch -> re-apply -> zip.

    python -X utf8 tools/release.py [--version 1.0] [--force]

Stops at the first failure. Writes release/LoGH_EN_vX.Y.bps, release/README.txt and release/LoGH_EN_vX.Y.zip
(patch + README + font licence). The playable image stays in build/logh_en.sfc. Never publishes anything.
"""
import argparse, hashlib, subprocess, sys, zipfile, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORIG = ROOT / 'rom' / 'Ginga Eiyuu Densetsu (Japan).sfc'
BUILT = ROOT / 'build' / 'logh_en.sfc'
SKILL = Path(subprocess.check_output([sys.executable, str(ROOT / 'tools' / 'skill.py')], text=True).strip())
PY = [sys.executable, '-X', 'utf8']


def run(name, cmd):
    print(f'== {name}', flush=True)
    if subprocess.run(cmd, cwd=ROOT).returncode:
        sys.exit(f'release: {name} failed')


def hashes(data):
    return (f'CRC32 {zlib.crc32(data):08X}, MD5 {hashlib.md5(data).hexdigest()}, '
            f'SHA-1 {hashlib.sha1(data).hexdigest()}')


README = """Legend of the Galactic Heroes (Ginga Eiyuu Densetsu) - English translation v{ver}
Super Famicom, Tokuma Shoten 1992. Unofficial fan translation.

APPLYING
Apply LoGH_EN_v{ver}.bps with Flips, beat or https://www.marcrobledo.com/RomPatcher.js/ to:
  Ginga Eiyuu Densetsu (Japan).sfc  (No-Intro; 1,048,576 bytes, no copier header)
  {orig}
Patched ROM: {built}
If your file is 1,049,088 bytes it has a 512-byte copier header: remove it first.

NOTES
- Tested in Mesen 2.2.1. Start from a cold boot; savestates from the Japanese ROM will show wrong text.
- Known issues: none. Report bugs: https://github.com/minhnhattonthat/ginga-eiyuu-densetsu-en/issues

CREDITS
Translation and hacking: minhnhattonthat. Made with extensive AI assistance (Claude by Anthropic).
Font: Ark Pixel (OFL). Ginga Eiyuu Densetsu (c) Tokuma Shoten; not affiliated.
No ROMs are distributed. Do not share patched ROMs.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', default='1.0')
    ap.add_argument('--force', action='store_true', help='overwrite this version\'s files')
    a = ap.parse_args()
    out = ROOT / 'release'
    bps = out / f'LoGH_EN_v{a.version}.bps'
    zp = out / f'LoGH_EN_v{a.version}.zip'
    if (bps.exists() or zp.exists()) and not a.force:
        sys.exit(f'release: {bps.name} already exists (--force to overwrite)')
    out.mkdir(exist_ok=True)

    # plain build: no --marker/--qa, and the debug warp is Lua only (tools/debug), never in the ROM
    run('build', PY + ['tools/build.py'])
    run('check', PY + ['tools/check.py'])
    run('smoke', PY + [str(SKILL / 'scripts/emu.py'), str(BUILT), '--out', 'work/qa/smoke',
                       '--route', 'tools/routes/boot.txt', '--smoke'])
    # text regions only (a 1-byte encoding makes every bank decode as kana); 0x2FF00 is the sub pointer table
    run('jp_left', PY + [str(SKILL / 'scripts/jp_left.py'), str(BUILT), '--orig', str(ORIG), '--tbl', 'tbl/jp.tbl',
                         '--range', '28476-2FFFF', '--range', '103BB-1081B', '--known', 'tools/jp_left_known.txt'])
    run('qa_gate', PY + [str(SKILL / 'scripts/qa_gate.py'), 'check', 'work/qa/manifest.tsv', 'work/qa/verdicts'])
    run('patch', PY + ['tools/bps.py', 'make', str(ORIG), str(BUILT), str(bps)])

    check = out / 'reapply.sfc'
    run('re-apply', PY + ['tools/bps.py', 'apply', str(ORIG), str(bps), str(check)])
    built = BUILT.read_bytes()
    if check.read_bytes() != built:
        sys.exit('release: re-applied patch differs from build/logh_en.sfc')
    check.unlink()

    readme = out / 'README.txt'
    readme.write_text(README.format(ver=a.version, orig=hashes(ORIG.read_bytes()), built=hashes(built)),
                      encoding='utf-8', newline='\r\n')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(bps, bps.name)
        z.write(readme, 'README.txt')
        z.write(ROOT / 'fonts' / 'OFL-ark-pixel.txt', 'OFL-ark-pixel.txt')  # the OFL must ship with the embedded font
    print(f'release ok: {zp.relative_to(ROOT)} ({zp.stat().st_size} bytes)')


if __name__ == '__main__':
    main()
