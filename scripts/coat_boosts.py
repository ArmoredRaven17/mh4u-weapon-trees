"""Which coating each MH4U bow boosts, read from the game, for the COAT_BOOSTS block in docs/index.html.

    python scripts/coat_boosts.py [C:\\MH4U-Extract]

Prints a JS object {bow id: coating name}, ids as the MH4U Collection Tracker keys them (the bow's
record index). Paste it over the object in the COAT_BOOSTS line; build.py never touches that line.

READ (2026-10-16), the bow's "Coating Boosts" readout at 0x27efa4:
  - the u64 at +0x20 of the bow's record, READ 0x2f5bc4 (non-relic branch 0x2f5c68: table
    [0xf588a0 + 4 * class - 0x1c] = 0xf58884 + 4 * 16, record = id * 0x28, ldrd [rec + 0x20]) --
    the same word whose bits k + 1 are the coatings (0xed2bd8, READ 0x27d558);
  - tested against the six masks at 0xed2c20 in order; the first set one shows Menu[u32 0xed2c08[i]]
    under the heading Menu 0x236 "Coating Boosts", none shows Menu 0x227 "(None)".
  0x200 Poison, 0x400 Paralysis, 0x800 Sleep, 0x1000 Exhaust, 0x4000 Blast, 0x8000 C.Range.
  On every bow at most one is set, and only ever on a coating that bow has. Relics take another
  table (0xf3f5dc) and are not in the tracker, so not here.
"""
import json, os, struct, sys

EXTRACT = sys.argv[1] if len(sys.argv) > 1 else r'C:\MH4U-Extract'
CODE = open(os.path.join(EXTRACT, 'exefs', 'code.decompressed.bin'), 'rb').read()
BASE = 0x100000
GUNNER_TABLES, COUNTS, BOW = 0xf58884, 0xf3fc38, 16
BOOST_MSG, BOOST_MASK = 0xed2c08, 0xed2c20
# Menu 0x220-0x226: the coating names as the readout spells them (the same ids as Menu 543 + k).
MENU_NAME = {0x220: 'Poison', 0x221: 'Paralysis', 0x222: 'Sleep', 0x223: 'C.Range',
             0x225: 'Exhaust', 0x226: 'Blast'}


def word(va):
    return struct.unpack_from('<I', CODE, va - BASE)[0]


def main():
    tab, n = word(GUNNER_TABLES + 4 * BOW), word(COUNTS + 4 * BOW)
    boosts = [(word(BOOST_MASK + 4 * i), MENU_NAME[word(BOOST_MSG + 4 * i)]) for i in range(6)]
    out = {}
    for i in range(1, n):
        bits = struct.unpack_from('<Q', CODE, tab + i * 0x28 + 0x20 - BASE)[0]
        hit = [name for mask, name in boosts if bits & mask]
        if hit:
            out[i] = hit[0]
    print(json.dumps(out, separators=(',', ':')))


if __name__ == '__main__':
    main()
