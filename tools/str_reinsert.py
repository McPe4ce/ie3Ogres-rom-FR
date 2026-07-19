"""Apply translated text from a str_dump.py JSON back into a NEW .STR file.

Strategy (safe, evet-style): the original .STR is the byte-exact base. For each
edited entry we replace that record's text with encode_text(fr) and re-pad it to
the next 0x20 boundary (matching the convention of the fully-untranslated target
files). Unedited records keep their original bytes verbatim, so a no-op reinsert
reproduces the original .STR byte-for-byte. Record COUNT and ORDER are always
preserved — the two invariants the game's ordinal lookup actually depends on.
There is NO per-record budget: .STR strings may grow or shrink freely.

Usage:
  python3 str_reinsert.py trans.json [--out name_new.STR] [--dir DIR] [--dry-run]
"""
import json, argparse
from str_slots import load, build_str, _align_up, LOGIC
from ie3_codec import encode_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--dir", default=LOGIC)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    doc = json.load(open(args.json, encoding="utf-8"))
    name = doc["file"]
    data, records = load(name, args.dir)  # records: list of (text, pad_len)
    records = list(records)

    if len(records) != doc.get("records", len(records)):
        print(f"  ! record count mismatch: JSON expects {doc.get('records')}, "
              f"file has {len(records)} — aborting (wrong file/version?).")
        return

    edits = 0; skipped = 0
    fold_report = {}
    for e in doc["entries"]:
        fr = e.get("fr", "")
        cls = e["cls"]
        # decide whether this entry is a real change
        if cls == "jp":
            if not fr.strip():
                continue
        else:
            if fr == e.get("src", "") or not fr:
                continue
        idx = e["idx"]
        try:
            enc, folds = encode_text(fr)
        except ValueError as ex:
            print(f"  ! idx {idx}: {ex} — skipped")
            skipped += 1
            continue
        if folds:
            for ch, rep in folds:
                fold_report[ch] = fold_report.get(ch, 0) + 1
        # re-pad the edited record to the next 0x20 boundary
        pad = _align_up(len(enc) + 1) - (len(enc) + 1)
        records[idx] = (enc, pad)
        edits += 1

    print(f"applied {edits} edits ({skipped} skipped for encode errors)")
    if fold_report:
        print("  house-style folds applied (accent/ligature -> ASCII):", fold_report)

    rebuilt = build_str(records)
    same = rebuilt == data
    if args.dry_run:
        print(f"dry-run: would write {len(rebuilt)} bytes"
              f"{' (identical to original)' if same else ''}. Nothing written.")
        return
    out = args.out or f"{name}_new.STR"
    with open(out, "wb") as f:
        f.write(rebuilt)
    print(f"wrote {out} ({len(rebuilt)} bytes)"
          f"{' — identical to original (no effective change)' if same else ''}")


if __name__ == "__main__":
    main()
