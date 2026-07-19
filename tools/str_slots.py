"""Byte-exact model of a .STR flat string pool (data_iz/logic/*.STR).

A .STR is a sequence of 32-byte-aligned records. Each record is:
    [text bytes (no 0x00)] [0x00 terminator] [zero-pad up to the next 0x20]
A long string simply spans several 0x20 blocks before its terminator; the
next record still begins on the following 0x20 boundary. The file may open
with an empty record (a 0x00 at offset 0, e.g. item.STR's leading zero block).

Lookup in-game is by ORDINAL INDEX (no offset table exists anywhere — see
docs/FORMAT_NOTES.md), so strings can be freely resized as long as the four
invariants hold: (1) record count, (2) order, (3) one 0x00 terminator each,
(4) each record starts on a 0x20 boundary. This model preserves all four and
round-trips byte-for-byte; editing rebuilds a record as text+0x00+pad without
disturbing any other record's index.

CLI:  python3 str_slots.py item           # round-trip self-test + census
      python3 str_slots.py item unitbase
"""
import sys

LOGIC = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/logic/"
ALIGN = 0x20


def _align_up(x, a=ALIGN):
    return (x + a - 1) // a * a


def parse_str(data):
    """Return a list of records: (start_offset, text_bytes, pad_len).

    A record is `text` + one 0x00 terminator + `pad_len` trailing 0x00 bytes.
    Padding is captured EXACTLY (not assumed): after the terminator we consume
    only the 0x00 bytes up to the next 0x20 boundary — so aligned files gain
    per-record padding, while a tight-packed string (next record begins at a
    non-boundary, as in games.STR) gets pad_len=0. This round-trips every file.
    """
    recs = []
    i, n = 0, len(data)
    while i < n:
        start = i
        j = i
        while j < n and data[j] != 0:
            j += 1
        text = bytes(data[start:j])
        if j >= n:
            # No terminator before EOF: record the remainder with no terminator.
            recs.append((start, text, None))  # None => unterminated tail
            break
        # Consume 0x00 padding up to (but not across) the next 0x20 boundary.
        boundary = _align_up(j + 1)
        k = j + 1
        while k < boundary and k < n and data[k] == 0:
            k += 1
        recs.append((start, text, k - (j + 1)))
        i = k
    return recs


def build_str(records):
    """Rebuild file bytes from records = list of (text_bytes, pad_len).
    Each record: text + 0x00 terminator + pad_len*0x00 (pad_len None = tail,
    no terminator)."""
    out = bytearray()
    for text, pad_len in records:
        assert 0 not in text, "record text must not contain a 0x00 byte"
        out += text
        if pad_len is None:
            continue
        out += b"\x00"
        out += b"\x00" * pad_len
    return bytes(out)


def load(name, logic=LOGIC):
    """Load name.STR, parse, and assert byte-exact round-trip.
    Returns (raw_bytes, records) where records is a list of (text_bytes, pad_len)."""
    data = open(logic + name + ".STR", "rb").read()
    parsed = parse_str(data)
    records = [(t, p) for _off, t, p in parsed]
    rebuilt = build_str(records)
    assert rebuilt == data, (
        f"{name}.STR round-trip FAILED: rebuilt {len(rebuilt)} vs original "
        f"{len(data)} bytes")
    return data, records


def _census(records):
    """Classify records for a quick summary (reuses the STR heuristics)."""
    texts = [t for t, _p in records]
    def looks_sjis_jp(b):
        hits, k = 0, 0
        while k < len(b) - 1:
            lo = b[k]
            if 0x81 <= lo <= 0x9f or 0xe0 <= lo <= 0xef:
                tr = b[k + 1]
                if 0x40 <= tr <= 0xfc and tr != 0x7f:
                    hits += 1; k += 2; continue
            k += 1
        return hits >= 2
    jp = fr = empty = ascii_only = 0
    for b in texts:
        if not b:
            empty += 1
        elif looks_sjis_jp(b):
            jp += 1
        elif any(x >= 0x80 for x in b):
            fr += 1
        else:
            ascii_only += 1
    return {"jp": jp, "fr": fr, "ascii": ascii_only, "empty": empty}


def main(name):
    data, records = load(name)
    print(f"=== {name}.STR ===  {len(data)} bytes, {len(records)} records "
          f"(round-trip OK)")
    print(f"  census: {_census(records)}")


if __name__ == "__main__":
    for nm in (sys.argv[1:] or ["item", "unitbase"]):
        main(nm)
