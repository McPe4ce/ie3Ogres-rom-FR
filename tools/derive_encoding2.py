"""Refined encoding derivation. Distinguishes:
  - LEADING byte of each chunk (position 0) = opaque control/box code
  - 0x81-prefixed two-byte symbols (leftover full-width SJIS punctuation)
  - INTERIOR high bytes = the actual accented-letter encoding we want
Also decodes 0x81xx pairs as shift-jis to identify the symbols."""
import sys
from collections import Counter, defaultdict
from evet_extract import parse_evet

# Working hypothesis table (interior high byte -> French char), filled from
# derive_encoding.py output. Update as confirmed.
KNOWN = {
    0xBA: "é", 0xB1: "à", 0xBB: "ê", 0xB9: "è", 0xB8: "ç",
    0xC5: "ô", 0xB3: "â", 0xC9: "Ù", 0xCB: "û", 0xBF: "î",
}

def render(raw):
    out = []
    for c in raw:
        if 0x20 <= c < 0x7f:
            out.append(chr(c))
        elif c in KNOWN:
            out.append(KNOWN[c])
        else:
            out.append(f"<{c:02X}>")
    return "".join(out)

def main():
    lead = Counter()
    interior = Counter()
    ctx = defaultdict(list)
    pair81 = Counter()
    pair81_ctx = defaultdict(list)
    for e in parse_evet("evet"):
        if e["cls"] != "fr":
            continue
        raw = e["raw"]
        if raw and raw[0] >= 0x80:
            lead[raw[0]] += 1
        k = 0
        while k < len(raw):
            c = raw[k]
            if c == 0x81 and k+1 < len(raw):
                nb = raw[k+1]
                pair81[nb] += 1
                if len(pair81_ctx[nb]) < 4:
                    lo = max(0, k-10)
                    pair81_ctx[nb].append(render(raw[lo:k]) + f"<81 {nb:02X}>" + render(raw[k+2:k+12]))
                k += 2
                continue
            if c >= 0x80 and k != 0:
                interior[c] += 1
                if len(ctx[c]) < 6:
                    lo, hi = max(0, k-14), min(len(raw), k+15)
                    ctx[c].append(render(raw[lo:k]) + f"[{c:02X}]" + render(raw[k+1:hi]))
            k += 1

    print("=== LEADING control/box codes (position 0), preserve opaque ===")
    print("  " + ", ".join(f"{b:02X}({c})" for b, c in sorted(lead.items())))

    print("\n=== 0x81-prefixed two-byte symbols ===")
    for nb, cnt in pair81.most_common():
        try:
            sj = bytes([0x81, nb]).decode("shift_jis")
        except Exception:
            sj = "?"
        print(f"  0x81 {nb:02X}  x{cnt:5d}  sjis={sj!r}   " + "  ".join(pair81_ctx[nb][:3]))

    print("\n=== INTERIOR high bytes (the letter table) ===")
    for b, cnt in interior.most_common():
        tag = f" = '{KNOWN[b]}'" if b in KNOWN else "  <-- UNMAPPED"
        print(f"0x{b:02X} x{cnt:6d}{tag}")
        if b not in KNOWN:
            for s in ctx[b][:6]:
                print(f"        {s}")

if __name__ == "__main__":
    main()
