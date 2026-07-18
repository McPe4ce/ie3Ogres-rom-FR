---
name: ie3-str-format
description: Use when analyzing or editing .STR flat string pool files in this Inazuma Eleven 3 ROM project (data_iz/logic/*.STR — item.STR, unitbase.STR, command.STR, games.STR, rpgtitle.STR, sp_binder.STR, tacticscmd.STR). Triggers on requests like "translate the item descriptions", "what's in unitbase.STR", "edit the player names", "parse this STR file", or any mention of the game's flat string table format. Also use before writing new .STR parsing/editing code.
---

# IE3 `.STR` Flat String Pool Format

`.STR` files under `data_iz/logic/` hold simpler tabular text than the
`.pkb`/`.pkh` script archives (see the `ie3-pkb-pkh-format` skill for
those) — things like item descriptions and the player roster, not branching
dialogue.

## What's confirmed (from hex-dumping `item.STR`)

- **No file header.** Content is a sequence of null-terminated strings
  concatenated directly, starting at byte 0.
- **32-byte alignment.** After a string's `0x00` terminator, zero-padding
  fills up to the next multiple of `0x20` before the next string begins.
  Confirmed across the first 15 entries of `item.STR` (offsets 0x20, 0x60,
  0xA0, 0x100, 0x1E0, ... — all multiples of 0x20, gaps vary because a
  string that needs more than 32 bytes just spans multiple blocks). This is
  **not** a fixed-size-slot format like `.pkb` budgets — a string can be
  any length, it just always starts aligned.
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
(longer or shorter) as long as you preserve all four invariants:
1. total **string count** unchanged (don't add/remove strings),
2. string **order** unchanged,
3. exactly one `0x00` **terminator** per string,
4. each string's start stays **32-byte aligned** (pad with `0x00` up to the
   next 0x20 boundary after each terminator).

Do not rely on staying within the original block span — that's unnecessary
now; full resizing is safe under the four invariants above.

## Practical guidance

- `item.STR` (822 strings) and `unitbase.STR` (2,374 strings) are currently
  **100% untranslated Japanese SJIS** (verified by
  `tools/verify_str_align.py` — every string classifies as SJIS, none are
  already French, all are 32-byte aligned). So every entry is available to
  translate; there's no partial-translation state to work around.
- `unitbase.STR` (player roster) is large and repetitive — a good first
  bulk target once the extraction/reinsertion tooling exists.
- Always re-run `verify_str_align.py` after any edit to confirm the four
  invariants still hold before repacking.
