"""Dump translatable text from a .pkb/.pkh text pair to an editable JSON file.

Each entry is one text sub-string (chunk), addressed by (rec, part) so
reinsertion can apply edits back onto the original slot. The leading box/
speaker control byte is handled automatically by the reinserter (it is NOT
part of the editable text). For Japanese entries, `src` is the Shift-JIS
source to translate and `fr` starts empty. For already-French entries, `fr`
is prefilled with the current text so leaving it unchanged is a no-op.

Edit the `fr` fields, then run evet_reinsert.py.

Usage:
  python3 evet_dump.py [name] [--jp-only] [-o out.json]
"""
import sys, json, argparse
from evet_slots import load_slots, classify
from ie3_codec import decode_text

def sjis(b):
    return b.decode("shift_jis", errors="replace")

def slot_used(slot):
    """Bytes up to the last non-zero (what must fit within budget)."""
    r = slot.recompose()
    i = len(r)
    while i > 0 and r[i-1] == 0:
        i -= 1
    return i

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", default="evet")
    ap.add_argument("--jp-only", action="store_true",
                    help="only dump untranslated Japanese entries")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--dir", default="/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/")
    args = ap.parse_args()

    _, _, _, slots = load_slots(args.name, args.dir)
    entries = []
    for rec, (rid, off, bud, slot) in enumerate(slots):
        used = slot_used(slot)
        for part, (chunk, za) in enumerate(slot.parts):
            c = bytes(chunk)
            cls = classify(c)
            if cls not in ("jp", "fr", "ascii"):
                continue
            body = c[1:]  # drop the leading (mult-of-4) control byte
            if cls == "jp":
                src = sjis(body)
                fr = ""
            else:
                src = decode_text(body, control="token")
                fr = src
            if args.jp_only and cls != "jp":
                continue
            entries.append({
                "rec": rec, "id": f"0x{rid:08X}", "part": part, "cls": cls,
                "budget": bud, "slot_used": used,
                "lead": f"{c[0]:02X}",
                "src": src, "fr": fr,
            })
    out = args.out or f"{args.name}_translation{'_jp' if args.jp_only else ''}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"file": args.name, "count": len(entries), "entries": entries},
                  f, ensure_ascii=False, indent=1)
    from collections import Counter
    cc = Counter(e["cls"] for e in entries)
    print(f"wrote {out}: {len(entries)} entries {dict(cc)}")

if __name__ == "__main__":
    main()
