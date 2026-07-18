"""Apply translated text from an evet_dump.py JSON back into a .pkb file.

Strategy (safe, .pkh untouched): the original .pkb is the base. For each edited
entry we rebuild its chunk as [original leading control byte] + encode_text(fr),
adjusting the slot's zero-padding to keep the slot's byte span constant, so
every later slot stays at its original offset and the .pkh index needs no
changes. Each edited slot is checked against its .pkh budget; overflows are
reported and (by default) NOT written.

Usage:
  python3 evet_reinsert.py trans.json [--out evet_new.pkb] [--dir DIR]
                                       [--allow-overflow] [--dry-run]
The original .pkb/.pkh are read from --dir (default extracted script dir) using
the "file" recorded in the JSON; only a NEW .pkb is written (original untouched).
"""
import json, argparse
from evet_slots import load_slots
from ie3_codec import encode_text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--dir", default="/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/")
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-overflow", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    doc = json.load(open(args.json, encoding="utf-8"))
    name = doc["file"]
    pkh, pkb, recs, slots = load_slots(name, args.dir)

    # index slots by rec
    by_rec = {rec: slots[rec] for rec in range(len(slots))}

    edits = 0; skipped = 0
    fold_report = {}
    fit_fail = []
    for e in doc["entries"]:
        fr = e.get("fr", "")
        cls = e["cls"]
        # decide if this entry represents a change
        if cls == "jp":
            if not fr.strip():
                continue
        else:
            if fr == e.get("src", ""):
                continue
            if not fr:
                continue
        rid, off, bud, slot = by_rec[e["rec"]]
        chunk, za = slot.parts[e["part"]]
        lead = bytes([int(e["lead"], 16)])
        try:
            enc, folds = encode_text(fr)
        except ValueError as ex:
            print(f"  ! rec{e['rec']} part{e['part']}: {ex} — skipped")
            skipped += 1
            continue
        if folds:
            for ch, rep in folds:
                fold_report[ch] = fold_report.get(ch, 0) + 1
        new_chunk = lead + enc
        # how much the edit grows this chunk vs. the interior padding slack
        ok = slot.set_chunk_bytes(e["part"], new_chunk)
        if not ok:
            need = len(new_chunk) - len(bytes(chunk))
            fit_fail.append((e["rec"], e["part"], need))
        edits += 1

    # sanity: every slot must still recompose to exactly its budget
    for rec in range(len(slots)):
        rid, off, bud, slot = slots[rec]
        assert len(slot.recompose()) == bud, f"rec{rec} span changed!"

    print(f"applied {edits} edits ({skipped} skipped for encode errors)")
    if fold_report:
        print("  house-style folds applied (accent/ligature -> ASCII):", fold_report)
    if fit_fail:
        print(f"  !! {len(fit_fail)} edit(s) too long to fit their slot's budget "
              f"(rec, part, extra_bytes_needed): {fit_fail[:10]}")
        print("     -> shorten those French strings, or (advanced) grow the .pkh")
        print("        budget for that slot. Budgets are per-slot; see docs.")

    blocked = bool(fit_fail) and not args.allow_overflow
    if args.dry_run:
        print("dry-run: nothing written.")
        return
    if blocked:
        print("NOT writing: fix overflows or pass --allow-overflow. Original untouched.")
        return

    rebuilt = bytearray(pkb)
    for rid, off, bud, slot in slots:
        rebuilt[off:off+slot.span] = slot.recompose()
    out = args.out or f"{name}_new.pkb"
    with open(out, "wb") as f:
        f.write(rebuilt)
    same = bytes(rebuilt) == pkb
    print(f"wrote {out} ({len(rebuilt)} bytes){' — identical to original (no effective change)' if same else ''}")

if __name__ == "__main__":
    main()
