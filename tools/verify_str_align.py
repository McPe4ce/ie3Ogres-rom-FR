"""Confirm .STR invariants across the WHOLE file (not just first entries):
  - every string starts on a 32-byte boundary
  - classify each string as SJIS-Japanese vs custom-single-byte (French)
    to confirm the file is a partially-translated mix of variable lengths.
A file that is a working mix of variable-length JP and FR strings, with no
offset table in its .dat, can only be looked up by ordinal index -> resizing
is safe if count/order/alignment preserved."""
import sys

LOGIC = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/logic/"

def parse(path):
    data = open(path, "rb").read()
    ents, i, n = [], 0, len(data)
    while i < n:
        while i < n and data[i] == 0:
            i += 1
        if i >= n: break
        j = i
        while j < n and data[j] != 0:
            j += 1
        ents.append((i, data[i:j]))
        i = j
    return data, ents

def looks_sjis_jp(b):
    """True if the string contains >=2 valid SJIS kana/kanji lead+trail pairs."""
    hits = 0; k = 0
    while k < len(b)-1:
        lo = b[k]
        if 0x81 <= lo <= 0x9f or 0xe0 <= lo <= 0xef:
            tr = b[k+1]
            if 0x40 <= tr <= 0xfc and tr != 0x7f:
                hits += 1; k += 2; continue
        k += 1
    return hits >= 2

def main(name):
    data, ents = parse(LOGIC + name + ".STR")
    misaligned = [off for off, _ in ents if off % 0x20 != 0]
    jp = fr = ascii_only = 0
    for off, b in ents:
        if looks_sjis_jp(b):
            jp += 1
        elif any(x >= 0x80 for x in b):
            fr += 1          # high bytes but not SJIS pairs -> custom FR encoding
        else:
            ascii_only += 1
    print(f"=== {name}.STR ===  strings={len(ents)}")
    print(f"  misaligned (not on 0x20 boundary): {len(misaligned)}"
          + (f"  e.g. {[hex(x) for x in misaligned[:5]]}" if misaligned else "  -> ALL aligned"))
    print(f"  classified: SJIS-Japanese={jp}  custom/French(high-byte)={fr}  ascii-only={ascii_only}")
    # show a couple of French-looking samples decoded loosely as latin-1
    shown = 0
    for off, b in ents:
        if not looks_sjis_jp(b) and any(x >= 0x80 for x in b):
            print(f"    FR@{off:#06x} latin1={b[:40].decode('latin-1')!r}")
            shown += 1
            if shown >= 3: break

if __name__ == "__main__":
    for name in (sys.argv[1:] or ["item", "unitbase"]):
        main(name); print()
