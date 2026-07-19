---
name: ie3-str-format
description: Use when analyzing or editing .STR flat string pool files in this Inazuma Eleven 3 ROM project (data_iz/logic/*.STR — item.STR, unitbase.STR, command.STR, games.STR, rpgtitle.STR, sp_binder.STR, tacticscmd.STR). Triggers on requests like "translate the item descriptions", "what's in unitbase.STR", "edit the player names", "parse this STR file", or any mention of the game's flat string table format. Also use before writing new .STR parsing/editing code.
---

# IE3 `.STR` Flat String Pool Format

`.STR` files under `data_iz/logic/` hold simpler tabular text than the
`.pkb`/`.pkh` script archives (see the `ie3-pkb-pkh-format` skill for
those) — things like item descriptions and the player roster, not branching
dialogue.

## What's confirmed (byte-exact model round-trips all 7 `.STR` files)

- **No file header.** Content is a sequence of null-terminated strings
  concatenated directly, starting at byte 0.
- **32-byte alignment is a per-file CONVENTION, not a universal invariant.**
  In the fully-Japanese files (`item`, `unitbase`, `command`) every string
  starts on a `0x20` boundary — after a terminator, zero-padding fills to the
  next multiple of `0x20`. **But partially-translated files pack strings
  tight**: in `games.STR` some French strings begin immediately after the
  previous terminator with **no** alignment padding (verified — the byte-exact
  round-trip broke until the model stopped assuming alignment). So do **not**
  hard-code alignment; capture the *actual* padding per record.
  `tools/str_slots.py` does this and round-trips all seven `.STR` files exactly.
- Several files are **fixed-size 1024-record index tables** (`item` and
  `command` both have exactly 1024 records — 822/793 used strings + empty
  padding records), reinforcing ordinal indexing.
- **Encoding**: untranslated entries are Shift-JIS; translated entries use
  the same custom single-byte encoding as `.pkb` text (see the
  `ie3-french-encoding` skill) — detect per-string, don't assume one
  encoding for the whole file. (Note: `games.STR` also uses UTF-8 for a few
  punctuation marks like `°`; another reason to detect per-string.)
- **Encoding**: untranslated entries are Shift-JIS; translated entries use
  the same custom single-byte encoding as `.pkb` text (see the
  `ie3-french-encoding` skill) — detect per-string, don't assume one
  encoding for the whole file.
- Japanese source text includes furigana-style markup like `[水/みず]`
  (kanji `/` reading, in brackets) — likely stripped/specially rendered by
  the game's text engine, not literal brackets. French replacements
  presumably don't need this, but **unconfirmed** whether the renderer
  tolerates its absence gracefully — test in an emulator before assuming.

## Indexing mechanism — RESOLVED: ordinal index, resizing is safe

Confirmed 2026-07-18 (`tools/analyze_str_dat.py`, `analyze_str_dat2.py`,
`find_offset_table.py`; see `docs/FORMAT_NOTES.md` for the full write-up).
The game looks entries up by **ordinal index** (Nth string), **not** by byte
offset:

- `item.dat`/`unitbase.dat` contain no plaintext offset table into their
  `.STR` (raw u32 offset matches in `item.dat` = 0; no monotonic offset/
  index column at any record size).
- `find_offset_table.py` searched **all 1,987 extracted files** for
  `item.STR`'s exact offset sequence (as raw u32/u16 offsets, `offset>>5`
  block indices, and length deltas) and found it **nowhere** — so there is
  no offset table for the loader to read; it must count null terminators at
  load time.

**Safe editing rule:** you may re-translate and freely resize strings
(longer or shorter) as long as you preserve the invariants the game's ordinal
lookup actually depends on:
1. total **record count** unchanged (don't add/remove strings/terminators),
2. record **order** unchanged,
3. exactly one `0x00` **terminator** per record.

Alignment is handled automatically by the tooling (unedited records keep their
exact original padding; edited records are re-padded to the `0x20` boundary,
matching the untranslated files' convention). Full resizing is safe — there is
no per-record byte budget.

## Tooling (built 2026-07-19 — use these; don't re-derive)

Run from `tools/` with the venv active. Mirrors the `evet` pipeline:

```bash
python3 str_slots.py item unitbase      # byte-exact round-trip self-test + census
python3 str_dump.py item --jp-only -o item_jp.json   # dump translatable strings
#  ... edit the "fr" field of each entry ...
python3 str_reinsert.py item_jp.json --out item_new.STR   # NEW .STR, original untouched
python3 repack_rom.py -r data_iz/logic/item.STR=item_new.STR -o patched.nds --verify
```

- `str_slots.py` — byte-exact model (`load`, `parse_str`, `build_str`). A no-op
  reinsert reproduces the original `.STR` byte-for-byte (the correctness check).
- `str_dump.py` — dump non-empty records to editable JSON, addressed by ordinal
  `idx`; empty/padding records are skipped but their indices are preserved.
- `str_reinsert.py` — apply edits into a new `.STR`; preserves record count/order,
  re-pads edited records, reports house-style accent folds. No budget check
  (resizing is free).

## Practical guidance

- `item.STR` (822 strings) and `unitbase.STR` (2,374 strings) are currently
  **100% untranslated Japanese SJIS**, so every entry is available to translate;
  no partial-translation state to work around.
- `unitbase.STR` (player roster) is large and repetitive — a good first
  bulk target.
- A no-op `str_reinsert` (or `str_slots.py <name>`) is the fast integrity check
  after any edit: it must report byte-identical / round-trip OK before repacking.
- `verify_str_align.py` remains for classification/alignment inspection, but note
  its "all aligned" report only holds for the untranslated files (see above).
