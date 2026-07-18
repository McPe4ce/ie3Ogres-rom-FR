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

## What's NOT yet confirmed — investigate before editing

**How entries get looked up.** `item.STR` has a same-named sibling
`item.dat` presumed to hold structured records (price, stats, sprite ID,
...) that likely reference the description text somehow. This matters a
lot for editing safety:

- If the reference is a **byte offset** into `item.STR`, resizing any
  string requires also patching every downstream offset in `item.dat` (and
  anything else that references entries after the one you resized).
- If the reference is a **sequential index** (e.g. the game just counts
  null terminators at load time to find the Nth entry), then resizing is
  safe as long as string **count and order** are preserved — you can freely
  change length.

**Do not assume either answer — check `item.dat`'s structure first**
(dump it, look for plausible offset-sized integers that land on `item.STR`'s
32-byte-aligned boundaries, or for small sequential integers that look like
indices instead). The same question applies to `unitbase.STR` and its
likely sibling `.dat`/logic table, and to the other `.STR` files. No script
exists yet for this — see `docs/FORMAT_NOTES.md` → "`.STR` flat string pool
format" and the open-questions list for the current state, and update that
doc (not just this skill) once resolved.

## Practical guidance

- Given the indexing question is open, the **safest first edits** are ones
  where you keep the replacement string the same byte length or shorter
  than the original within its 32-byte-aligned block span (i.e. it still
  fits in the same number of 0x20 blocks) — this sidesteps the whole
  offset-relocation question regardless of which lookup mechanism turns out
  to be true, at the cost of being more space-constrained than necessary.
- `unitbase.STR` (player roster, 3,144 leftover Japanese runs per the last
  scan) is a much bigger and more repetitive dataset than `item.STR` — a
  good candidate to fully solve the indexing question on first, since
  getting it wrong at that scale is costly to redo.
