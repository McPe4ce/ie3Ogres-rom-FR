"""Dump translatable strings from a .STR flat string pool to editable JSON.

Each entry is one record, addressed by its ordinal `idx` (0-based record
position — the same ordinal the game uses to look strings up). Empty/padding
records are skipped in the dump but their indices are preserved, so reinsertion
never disturbs the record count or order. For Japanese entries `src` is the
Shift-JIS source and `fr` starts empty; for already-French entries `fr` is
prefilled with the current text (leaving it unchanged is a no-op).

Edit the `fr` fields, then run str_reinsert.py. Because .STR lookup is by
ordinal index (no offset table — see docs/FORMAT_NOTES.md), strings may be
freely resized; there is no per-record byte budget.

Usage:
  python3 str_dump.py item [--jp-only] [-o out.json]
"""
import json, argparse
from collections import Counter
from str_slots import load, LOGIC
from str_codec import decode_str_fr


def _has_real_jp(s):
    """True if the string contains kana or CJK kanji (genuinely untranslated).
    Full-width Latin decodes to SJIS pairs too but is already-translated French,
    so we key off actual Japanese script, not raw SJIS-pair presence."""
    return any('぀' <= c <= 'ヿ' or '一' <= c <= '鿿' or 'ｦ' <= c <= 'ﾝ'
               for c in s)


def classify(b):
    """jp (real kana/kanji -> translate) / fr (already full-width French) /
    ascii / empty."""
    if not b:
        return "empty"
    s = b.decode("shift_jis", errors="replace")
    if _has_real_jp(s):
        return "jp"
    return "fr" if any(x >= 0x80 for x in b) else "ascii"


def decode_src(b, cls):
    if cls == "jp":
        return b.decode("shift_jis", errors="replace")
    if cls == "fr":
        return decode_str_fr(b)   # already-French full-width -> readable ASCII
    return b.decode("ascii", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", default="item")
    ap.add_argument("--jp-only", action="store_true",
                    help="only dump untranslated Japanese entries")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--dir", default=LOGIC)
    args = ap.parse_args()

    _, records = load(args.name, args.dir)
    entries = []
    for idx, (text, _pad) in enumerate(records):
        cls = classify(text)
        if cls == "empty":
            continue
        if args.jp_only and cls != "jp":
            continue
        src = decode_src(text, cls)
        entries.append({
            "idx": idx, "cls": cls,
            "src": src,
            "fr": "" if cls == "jp" else src,
        })
    out = args.out or f"{args.name}_translation{'_jp' if args.jp_only else ''}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"file": args.name, "records": len(records),
                   "count": len(entries), "entries": entries},
                  f, ensure_ascii=False, indent=1)
    cc = Counter(e["cls"] for e in entries)
    print(f"wrote {out}: {len(entries)} translatable entries {dict(cc)} "
          f"(of {len(records)} total records)")


if __name__ == "__main__":
    main()
