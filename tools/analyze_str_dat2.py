"""Second pass: test compact reference encodings from .dat into .STR.
If the game references strings by *sequential index* (safe to resize) we
expect NO structured column of offsets/block-indices in .dat. If it uses
offsets we expect a column of either raw byte offsets, 16-bit offsets, or
block indices (offset>>5, since strings are 32-byte aligned)."""
import struct, sys
from collections import Counter

LOGIC = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/logic/"

def parse_str(path):
    data = open(path, "rb").read()
    entries, i, n = [], 0, len(data)
    while i < n:
        while i < n and data[i] == 0:
            i += 1
        if i >= n: break
        j = i
        while j < n and data[j] != 0:
            j += 1
        entries.append(i)
        i = j
    return data, entries

def main(name):
    sdata, starts = parse_str(LOGIC + name + ".STR")
    ddata = open(LOGIC + name + ".dat", "rb").read()
    startset = set(starts)
    blockset = set(s >> 5 for s in starts)   # 32-byte block index
    idxset = set(range(len(starts)))
    print(f"=== {name} ===  STR={len(sdata)} strings={len(starts)}  dat={len(ddata)}")

    def scan(width, fmt, label):
        hits_off = hits_blk = 0
        valpos = Counter()
        for off in range(0, len(ddata)-width+1):
            v = struct.unpack_from(fmt, ddata, off)[0]
            if v in startset: hits_off += 1
            if v in blockset and v != 0: hits_blk += 1
        print(f"  {label}: raw-offset matches={hits_off}  block-index(>>5) matches={hits_blk}")

    scan(4, "<I", "u32 LE")
    scan(2, "<H", "u16 LE")

    # How many DISTINCT block indices exist, and how many the dat hits, to
    # gauge whether block-index matches could form a real table (need ~= nstr)
    print(f"  distinct blocks={len(blockset)}  max block={max(blockset):#x}")

    # Is there a monotonic increasing u16 column (would indicate an index or
    # offset table laid out per-record)? Try a few record sizes.
    for rs in [rs for rs in range(4, 129) if len(ddata) % rs == 0]:
        recs = len(ddata)//rs
        if not (0.5 < recs/len(starts) < 2.5):
            continue
        for pos in range(0, min(rs-1, 8)):
            col = [struct.unpack_from('<H', ddata, r*rs+pos)[0] for r in range(recs)]
            monot = sum(1 for k in range(1, recs) if col[k] >= col[k-1])
            uniq = len(set(col))
            if monot > recs*0.9 and uniq > recs*0.5:
                print(f"  recsize={rs} col@{pos}: monotonic u16 ({monot}/{recs} nondecr, {uniq} uniq) "
                      f"first={col[:6]} last={col[-3:]}")

if __name__ == "__main__":
    for name in (sys.argv[1:] or ["item", "unitbase"]):
        main(name); print()
