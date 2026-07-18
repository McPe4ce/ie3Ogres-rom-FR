"""Decisive test for the .STR indexing mechanism.

If the game looks strings up by byte offset, an offset table must exist
SOMEWHERE (in the sibling .dat, another logic file, or arm9/overlay code).
Compute item.STR's exact string-start offset sequence, then search every
extracted file for that sequence appearing as consecutive u32/u16 LE values
(raw offset, or offset>>5 block index). If it appears nowhere, lookup is by
ordinal index and resizing is safe (given order/count/alignment preserved)."""
import os, struct

ROOT = "/home/mcpeace/ie3Ogres-rom-FR/extracted/"
LOGIC = ROOT + "data_iz/logic/"

def str_starts(path):
    data = open(path, "rb").read()
    starts, i, n = [], 0, len(data)
    while i < n:
        while i < n and data[i] == 0: i += 1
        if i >= n: break
        j = i
        while j < n and data[j] != 0: j += 1
        starts.append(i); i = j
    return starts

def build_needles(starts, k=24):
    """Byte patterns for the first k offsets as consecutive LE integers."""
    seq = starts[:k]
    needles = {}
    needles["u32 raw offset"] = b"".join(struct.pack("<I", s) for s in seq)
    needles["u16 raw offset"] = b"".join(struct.pack("<H", s) for s in seq)
    needles["u32 block>>5"]   = b"".join(struct.pack("<I", s>>5) for s in seq)
    needles["u16 block>>5"]   = b"".join(struct.pack("<H", s>>5) for s in seq)
    # also the *deltas* (some tables store lengths, not absolute offsets)
    deltas = [seq[i+1]-seq[i] for i in range(len(seq)-1)]
    needles["u16 deltas"] = b"".join(struct.pack("<H", d) for d in deltas)
    return needles

def main():
    starts = str_starts(LOGIC + "item.STR")
    print(f"item.STR: {len(starts)} strings, first offsets {[hex(s) for s in starts[:6]]}")
    needles = build_needles(starts)
    for label, pat in needles.items():
        print(f"  needle [{label}] = {len(pat)} bytes")

    found_any = False
    nfiles = 0
    for dirp, _, files in os.walk(ROOT):
        for fn in files:
            fp = os.path.join(dirp, fn)
            try:
                blob = open(fp, "rb").read()
            except Exception:
                continue
            nfiles += 1
            for label, pat in needles.items():
                idx = blob.find(pat)
                if idx != -1:
                    print(f"  *** MATCH [{label}] in {os.path.relpath(fp, ROOT)} @ {idx:#x}")
                    found_any = True
    print(f"\nScanned {nfiles} files.")
    if not found_any:
        print("NO offset/length table for item.STR found anywhere in the extraction.")
        print("=> lookup is by ORDINAL INDEX; resizing is safe if string count,")
        print("   order, null-termination and 32-byte alignment are preserved.")

if __name__ == "__main__":
    main()
