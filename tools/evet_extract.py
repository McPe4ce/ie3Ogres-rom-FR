"""Slot-by-slot text extractor for evet.pkh / evet.pkb (the main event
dialogue archive). Parses the confirmed .pkh record table, reads each slot
from the .pkb, splits it into null-bounded text chunks, and classifies each
chunk as Japanese (SJIS) vs already-translated French (custom single-byte)
vs control-only noise.

Usable as a library (import parse_evet) or CLI (prints a summary + samples).

Chunk model (see docs/FORMAT_NOTES.md "The .pkb / .pkh format"):
  a slot = [pad] [prefix bytes incl. 0x00 0x00 0x00 / 0x04..] [text] 0x00 ...
We take each maximal run of non-zero bytes as a raw chunk. The chunk's first
byte is often a control/box-style code (e.g. '<' , 0x04); text follows.
"""
import struct, sys

DIR = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/"

def read_pkh(pkh):
    assert pkh[:8] == b"PackNum ", "bad magic"
    count, = struct.unpack_from("<H", pkh, 0x16)
    recs = []
    for i in range(count):
        rid, off, bud = struct.unpack_from("<III", pkh, 48 + i*12)
        recs.append((rid, off, bud))
    return recs

def sjis_pair_coverage(b):
    """Fraction of bytes consumed by valid *double-byte* SJIS lead+trail
    pairs (kana/kanji). High => Japanese text. Custom French high bytes
    (0xa0-0xff used as accents) are NOT valid lead bytes, so French chunks
    score ~0."""
    n = len(b)
    if n == 0:
        return 0.0
    consumed = 0; k = 0
    while k < n-1:
        lo = b[k]
        if (0x81 <= lo <= 0x9f) or (0xe0 <= lo <= 0xef):
            tr = b[k+1]
            if 0x40 <= tr <= 0xfc and tr != 0x7f:
                consumed += 2; k += 2; continue
        k += 1
    return consumed / n

def classify(chunk):
    """Return 'jp' | 'fr' | 'ctrl' | 'ascii'."""
    if len(chunk) <= 2 and all(c < 0x20 or c >= 0x80 for c in chunk):
        return "ctrl"
    if sjis_pair_coverage(chunk) >= 0.30:
        return "jp"
    # printable-ASCII dominant?
    printable = sum(1 for c in chunk if 0x20 <= c < 0x7f)
    if printable >= max(2, 0.5*len(chunk)):
        return "fr" if any(c >= 0x80 for c in chunk) else "ascii"
    return "ctrl"

def split_chunks(slot):
    """Yield (start_in_slot, raw_bytes) for each maximal non-zero run."""
    i, n = 0, len(slot)
    while i < n:
        while i < n and slot[i] == 0:
            i += 1
        if i >= n:
            break
        j = i
        while j < n and slot[j] != 0:
            j += 1
        yield i, slot[i:j]
        i = j

def parse_evet(name="evet"):
    pkh = open(DIR + name + ".pkh", "rb").read()
    pkb = open(DIR + name + ".pkb", "rb").read()
    recs = read_pkh(pkh)
    for ridx, (rid, off, bud) in enumerate(recs):
        slot = pkb[off:off+bud]
        for cidx, (cstart, raw) in enumerate(split_chunks(slot)):
            yield {
                "rec": ridx, "id": rid, "slot_off": off, "budget": bud,
                "chunk": cidx, "chunk_off": off + cstart,
                "raw": raw, "cls": classify(raw),
            }

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "evet"
    from collections import Counter
    cls_count = Counter()
    total = 0
    samples = {"jp": [], "fr": [], "ascii": [], "ctrl": []}
    for e in parse_evet(name):
        total += 1
        cls_count[e["cls"]] += 1
        if len(samples[e["cls"]]) < 6:
            samples[e["cls"]].append(e)
    print(f"{name}: {total} chunks -> {dict(cls_count)}")
    for cls in ("fr", "jp", "ascii", "ctrl"):
        print(f"\n--- {cls} samples ---")
        for e in samples[cls]:
            r = e["raw"]
            print(f"  rec{e['rec']} id={e['id']:#010x} off={e['chunk_off']:#x} "
                  f"len={len(r)} latin1={r[:48].decode('latin-1')!r}")

if __name__ == "__main__":
    main()
