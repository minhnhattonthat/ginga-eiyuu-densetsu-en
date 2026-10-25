"""gfx.py: the game's tile compression and graphics directory (docs/re/graphics.md).

Compression ($00:9272 2bpp, $00:92DD 3 planes -> 4bpp): per 8x8 tile, one mask byte per plane, then row bytes. Mask
bits MSB first, one per row: 1 = read a new byte, 0 = repeat the previous row of this plane (starts at 0).
2bpp tile = [m0 m1][rows p0 / p1 interleaved as they come]; output is SNES planar 2bpp (16 bytes per tile).
3-plane tile = [m0 m1 m2][rows]; output 4bpp (32 bytes), plane 3 = 0.

Directory: graphics id -> $07:82C8 + 4*id = (entry index, VRAM word/2); $07:8000 + 2*entry = (bank, slot);
bank:$8000 + 4*slot = (src addr, tile count).
    python -X utf8 tools/gfx.py list            # every (bank, slot) block with its plane count
    python -X utf8 tools/gfx.py sheets OUTDIR   # render every block (survey)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom" / "Ginga Eiyuu Densetsu (Japan).sfc"
BANKLIST = 0x38000


def lorom(bank, addr):
    return ((bank & 0x7F) << 15) | (addr & 0x7FFF)


def decompress(rom, off, tiles, planes):
    """Returns (planar tile bytes, bytes consumed). planes 2 -> 16 B/tile, planes 3 -> 32 B/tile."""
    out = bytearray()
    pos = off
    for _ in range(tiles):
        masks = rom[pos:pos + planes]
        pos += planes
        rows = [[0] * 8 for _ in range(planes)]
        # The game walks planes 0/1 row-interleaved per pair, but each plane reads its own bytes in order.
        for p in range(min(planes, 2)):
            prev = 0
            for r in range(8):
                if masks[p] & (0x80 >> r):
                    prev = rom[pos]; pos += 1
                rows[p][r] = prev
        if planes == 3:
            prev = 0
            for r in range(8):
                if masks[2] & (0x80 >> r):
                    prev = rom[pos]; pos += 1
                rows[2][r] = prev
        tile = bytearray()
        for r in range(8):
            tile += bytes([rows[0][r], rows[1][r]])
        if planes == 3:
            for r in range(8):
                tile += bytes([rows[2][r], 0])
        out += tile
    return bytes(out), pos - off


def compress(tiledata, planes):
    out = bytearray()
    step = 16 if planes == 2 else 32
    for t in range(0, len(tiledata), step):
        tile = tiledata[t:t + step]
        rows = [[tile[2 * r + p] for r in range(8)] for p in range(2)]
        if planes == 3:
            rows.append([tile[16 + 2 * r] for r in range(8)])
        masks, data = [], bytearray()
        for p in range(planes):
            m, prev = 0, 0
            for r in range(8):
                if rows[p][r] != prev:
                    m |= 0x80 >> r; data.append(rows[p][r]); prev = rows[p][r]
            masks.append(m)
        out += bytes(masks) + data
    return bytes(out)


def blocks(rom):
    """Every (bank, slot, src offset, tiles) the bank list reaches, sorted by offset."""
    banks = set()
    i = 0
    while BANKLIST + 2 * i < 0x382C8:
        banks.add((rom[BANKLIST + 2 * i], rom[BANKLIST + 2 * i + 1]))
        i += 1
    res = []
    for bank in sorted({b for b, _ in banks}):
        slots = max(s for b, s in banks if b == bank) + 1
        for s in range(slots):
            d = lorom(bank, 0x8000 + 4 * s)
            src, n = rom[d] | rom[d + 1] << 8, rom[d + 2] | rom[d + 3] << 8
            res.append((bank, s, lorom(bank, src), n))
    return sorted(res, key=lambda x: x[2])


def planes_of(rom, blist):
    """Guess planes per block: the count whose stream ends exactly where the next block starts."""
    out = []
    for k, (bank, s, off, n) in enumerate(blist):
        nxt = blist[k + 1][2] if k + 1 < len(blist) and blist[k + 1][0] == bank else None
        guess = None
        for p in (2, 3):
            try:
                _, used = decompress(rom, off, n, p)
            except IndexError:
                continue
            if nxt is not None and off + used == nxt:
                guess = p
        out.append(guess)
    return out


def main():
    rom = ROM.read_bytes()
    bl = blocks(rom)
    pl = planes_of(rom, bl)
    if sys.argv[1:2] == ["list"]:
        for (bank, s, off, n), p in zip(bl, pl):
            print("%02X:%02X %06X tiles=%4d planes=%s" % (bank, s, off, n, p))
    elif sys.argv[1:2] == ["sheets"]:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from PIL import Image
        outdir = Path(sys.argv[2]); outdir.mkdir(parents=True, exist_ok=True)
        for (bank, s, off, n), p in zip(bl, pl):
            p = p or 2
            data, _ = decompress(rom, off, n, p)
            cols = 16
            rows = (n + cols - 1) // cols
            img = Image.new("L", (cols * 8, rows * 8))
            step = 16 if p == 2 else 32
            for t in range(n):
                tile = data[t * step:(t + 1) * step]
                for r in range(8):
                    for c in range(8):
                        bit = 0x80 >> c
                        v = (1 if tile[2 * r] & bit else 0) | (2 if tile[2 * r + 1] & bit else 0)
                        if p == 3:
                            v |= 4 if tile[16 + 2 * r] & bit else 0
                        img.putpixel(((t % cols) * 8 + c, (t // cols) * 8 + r), 255 - v * (255 // (7 if p == 3 else 3)))
            img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
            img.save(outdir / ("%02X_%02X_%06X_p%d.png" % (bank, s, off, p)))
        print(f"{len(bl)} blocks -> {outdir}")


if __name__ == "__main__":
    main()
