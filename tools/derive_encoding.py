"""Derive the custom single-byte French encoding table from cleanly-bounded
evet French chunks. For every byte >=0x80 appearing in a 'fr'-classified
chunk, tally frequency and collect context snippets (the surrounding ASCII,
with the unknown byte shown as <XX>) so each accented character can be read
off from the French word it sits in."""
import sys
from collections import Counter, defaultdict
from evet_extract import parse_evet

def render(raw, hibyte_map=None):
    """Show a chunk as text: ASCII verbatim, known high bytes mapped, unknown
    high bytes as <XX>."""
    out = []
    for c in raw:
        if 0x20 <= c < 0x7f:
            out.append(chr(c))
        elif hibyte_map and c in hibyte_map:
            out.append(hibyte_map[c])
        else:
            out.append(f"<{c:02X}>")
    return "".join(out)

def main():
    freq = Counter()
    contexts = defaultdict(list)
    n_fr = 0
    for e in parse_evet("evet"):
        if e["cls"] != "fr":
            continue
        n_fr += 1
        raw = e["raw"]
        for pos, c in enumerate(raw):
            if c >= 0x80:
                freq[c] += 1
                if len(contexts[c]) < 8:
                    # context window of +-12 chars around the byte
                    lo, hi = max(0, pos-12), min(len(raw), pos+13)
                    snip = render(raw[lo:pos]) + f"[{c:02X}]" + render(raw[pos+1:hi])
                    contexts[c].append(snip)
    print(f"Analyzed {n_fr} French chunks; {len(freq)} distinct high-byte values.\n")
    print(f"{'byte':>4} {'count':>7}  context samples")
    for b, cnt in freq.most_common():
        print(f"0x{b:02X} {cnt:7d}  " + "   ".join(contexts[b][:5]))

if __name__ == "__main__":
    main()
