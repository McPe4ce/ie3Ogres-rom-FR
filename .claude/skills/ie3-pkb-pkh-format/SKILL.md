---
name: ie3-pkb-pkh-format
description: Use when analyzing, parsing, extracting text from, or editing .pkb/.pkh archive pairs in this Inazuma Eleven 3 ROM project (e.g. data_iz/script/evet.pkb, eve.pkh, mch.pkb, mcht.pkh, help.pkb). Triggers on requests like "extract the dialogue text", "parse this pkb file", "what's in evet.pkb", "how do I edit this pkh index", "add a translation to this event", or any mention of the "PackNum" archive format. Also use before writing any new .pkb/.pkh parsing or reinsertion code, to avoid re-deriving the format from scratch.
---

# IE3 `.pkb` / `.pkh` Archive Format ("PackNum")

This is a Level-5 proprietary archive format used throughout this ROM for
script/dialogue data — not just text: `data_iz/script/*.pkb`,
`data_iz/pic2d/cmd/*.pkb`, `data_iz/effect3d/eff.pkb`,
`data_iz/model/*/*.pkb`, etc. all use it. The format itself is generic
(an ID → offset → budget index over a data blob); what varies is what kind
of data lives in each blob.

**Read `docs/FORMAT_NOTES.md` (section "The `.pkb` / `.pkh` format
('PackNum')") before doing any real work here — it has the fully-verified
byte layout with worked examples.** This skill is a condensed pointer to
that, plus the operational guidance for using it.

## The condensed format (verified against `evet.pkh`/`evet.pkb`)

`.pkh` header (48 bytes) + record table:
```
0x00  16   magic "PackNum 20080626"
0x10   4   u32 LE — this .pkh file's own size (self-check: should equal len(file))
0x14   2   u16 LE — unknown (observed: 1)
0x16   2   u16 LE — record count
0x18   4   u32 LE — unknown (observed: 16)
0x1C   4   u32 LE — unknown (observed: 0x27D0)
0x20  16   reserved/zero
0x30  ...  record_count * 12-byte records
```
Each 12-byte record: `u32 ID, u32 offset_into_pkb, u32 byte_budget`.

- **ID** increases in clean arithmetic steps (e.g. 31010000, 31020000, ...)
  — an intentional scheme, not a hash. This is very likely what the
  companion script-logic file (`eve.pkb`, the non-`t`-suffixed sibling of
  `evet.pkb`) uses to reference a specific line, meaning text can be
  resized within its budget without touching script bytecode. **This
  inference is unconfirmed** — it hasn't been proven by reading `eve.pkb`
  bytecode directly. Don't stake anything irreversible on it without
  testing in an emulator first.
- **offset_into_pkb** is a direct byte offset into the paired `.pkb` file.
  Confirmed by direct read.
- **byte_budget** is the max size of that slot — varies per record, not
  fixed. This is the hard constraint for reinsertion: a replacement string
  (plus its framing bytes, see below) must fit within `byte_budget` bytes
  starting at `offset_into_pkb`.

`.pkb` has no file-level header — data starts at byte 0. A slot at
`(offset, budget)` can contain **multiple sub-strings** (e.g. all options
of one dialogue choice menu), each shaped:
```
[0x00 0x00 0x00]  [text bytes, may include control bytes]  [0x00 terminator]
```
with a short zero-padding gap before the next sub-string. Standalone bytes
like `0x04` appear as in-text control/formatting codes — treat them as
opaque, preserve verbatim, don't try to "translate" them. Text uses 2-byte
Shift-JIS for untranslated entries and a custom single-byte encoding for
already-translated French entries (see the `ie3-french-encoding` skill) —
detect which per sub-string, don't assume one encoding for a whole file.

## Working with this format

- `tools/inspect_pkh.py` and `tools/inspect_pkh2.py` are the reference
  implementations that established the above layout — use them as a
  starting template rather than re-deriving struct offsets from scratch.
  `inspect_pkh2.py` in particular shows how to read records and cross-check
  them against real `.pkb` bytes.
- **The extractor/reinserter now exist — use them, don't rewrite.**
  `tools/evet_slots.py` is the byte-exact slot model (`load_slots`, `Slot`);
  it round-trips all evet+mcht slots losslessly and conserves each slot's
  budget span, so the `.pkh` never needs editing. `tools/evet_dump.py` dumps
  translatable text to editable JSON; `tools/evet_reinsert.py` writes edited
  JSON back into a new `.pkb`, budget-checked (a no-op reinsert reproduces the
  original byte-for-byte). Text decode/encode is `tools/ie3_codec.py`.
  Key facts the model relies on (verified): a slot owns exactly `budget` bytes
  at `off` — the gap to the next record is `0x04 0xFF…` inter-slot filler, NOT
  the slot's; every sub-string's first byte is a box/speaker **control code**
  (always a multiple of 4) preserved automatically; the interior zero-padding
  is the slack an over-long translation grows into.
- Only `eve`/`evet` has been structurally verified. `mch`/`mcht`, `help`,
  `act`, `mr`, `mrobj` are presumed to follow the same `.pkb`/`.pkh` pattern
  (same magic string format) but this has **not** been individually
  confirmed — verify header/record parsing against each before trusting it,
  the same way `evet` was verified (cross-check declared record count
  against `(filesize - 48) / 12`, cross-check a record's offset+budget
  against a real hex dump).
- Files without a `t` suffix (`eve`, `mch`, `act`, `mr`, `mrobj`) are
  presumed to be script *bytecode*, not prose — don't run text-extraction
  heuristics (Japanese scanning, French context collection) against them,
  they'll produce binary-noise false positives. See the `ie3-french-encoding`
  skill for how this bit us once already.

## Open questions

See `docs/FORMAT_NOTES.md` → "Open questions / TODO" for the full list
(meaning of the unexplained header fields, meaning of the leading control
bytes in sub-strings, unconfirmed ID-based lookup). Update that file, not
just this skill, when any of these get resolved — `docs/FORMAT_NOTES.md` is
the source of truth, this skill is a summary of it.
