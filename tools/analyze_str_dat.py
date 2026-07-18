"""Investigate .STR indexing: are item.STR entries referenced by byte offset
or sequential index from item.dat? Parse item.STR string boundaries, then
scan item.dat for (a) offsets that land on those boundaries, or (b) small
sequential indices."""
import struct, sys

LOGIC = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/logic/"

def parse_str(path):
    """Return list of (index, start_offset, raw_bytes). Strings are
    null-terminated; the next string starts at the next non-zero byte
    (padding fills to a 0x20 boundary)."""
    data = open(path, "rb").read()
    entries = []
    i, n = 0, len(data)
    while i < n:
        while i < n and data[i] == 0:
            i += 1
        if i >= n:
            break
        start = i
        j = i
        while j < n and data[j] != 0:
            j += 1
        entries.append((len(entries), start, data[start:j]))
        i = j
    return data, entries

def main(name):
    sdata, entries = parse_str(LOGIC + name + ".STR")
    ddata = open(LOGIC + name + ".dat", "rb").read()
    nstr = len(entries)
    print(f"=== {name} ===")
    print(f"{name}.STR size={len(sdata)}  strings={nstr}")
    print(f"{name}.dat size={len(ddata)}  dat/strings={len(ddata)/nstr:.3f}")

    print("\nRecord-size candidates (dat size divisible, record count near string count):")
    cand_rs = []
    for rs in range(2, 513):
        if len(ddata) % rs == 0:
            recs = len(ddata)//rs
            if recs == nstr:
                print(f"  recsize {rs:3d} -> {recs} records  <-- EQUALS string count")
                cand_rs.append(rs)
            elif abs(recs-nstr) <= 3:
                print(f"  recsize {rs:3d} -> {recs} records  (off by {recs-nstr})")
                cand_rs.append(rs)

    starts = set(s for _, s, _ in entries)
    start_list = [s for _, s, _ in entries]
    print(f"\nFirst 10 string start offsets: {[hex(s) for s in start_list[:10]]}")

    hits = sum(1 for off in range(0, len(ddata)-3)
               if struct.unpack_from('<I', ddata, off)[0] in starts)
    print(f"u32 LE values anywhere in dat equal to a valid .STR start offset: {hits}")

    # For each plausible record size, test each field position as (a) offset
    # table or (b) sequential index.
    test_rs = cand_rs or [rs for rs in range(4, 257) if len(ddata) % rs == 0 and 0.3 < (len(ddata)//rs)/nstr < 3]
    for rs in test_rs:
        recs = len(ddata)//rs
        print(f"\n-- recsize={rs}, records={recs} --")
        for pos in range(0, rs-3):
            off_match = sum(1 for r in range(recs)
                            if struct.unpack_from('<I', ddata, r*rs+pos)[0] in starts)
            if off_match > recs*0.4:
                print(f"   field@{pos} (u32): {off_match}/{recs} are valid .STR offsets  <== OFFSET TABLE")
        for pos in range(0, rs-1):
            seq16 = sum(1 for r in range(recs)
                        if struct.unpack_from('<H', ddata, r*rs+pos)[0] == r)
            if seq16 > recs*0.4:
                print(f"   field@{pos} (u16): {seq16}/{recs} == record index  <== SEQUENTIAL INDEX")

if __name__ == "__main__":
    for name in (sys.argv[1:] or ["item", "unitbase"]):
        main(name)
        print()
