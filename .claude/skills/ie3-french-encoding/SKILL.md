---
name: ie3-french-encoding
description: Use when deriving, applying, or reasoning about the custom single-byte French character encoding used by this Inazuma Eleven 3 ROM's translated text — e.g. "decode this French string", "what character is byte 0xC9", "encode this translation back to game bytes", "build the character table", or any work that writes new French text into the ROM. Also use before attempting any fresh byte-frequency scan across ROM files, since two prior attempts were too noisy and the pitfalls are documented here.
---

# IE3 Custom French Character Encoding

**SOLVED 2026-07-18.** Use `tools/ie3_codec.py` (`decode_text` /
`encode_text`) — don't re-derive. The full confirmed table lives in
`docs/FORMAT_NOTES.md` ("Custom single-byte French character encoding —
SOLVED"). The rest of this skill explains the pitfalls of the earlier failed
attempts, kept because they're useful if this ever needs re-deriving (e.g.
for another Level-5 ROM).

The existing French patch text does **not** use standard Latin-1/CP1252
(byte `0xC9` = `ù`, not CP1252 `É`; `0xB1` = `à`, not `±`). The confirmed
single-byte accents (all **lowercase**) are: `0xB1`à `0xB3`â `0xB8`ç `0xB9`è
`0xBA`é `0xBB`ê `0xBF`î `0xC0`ï `0xC5`ô `0xC9`ù `0xCB`û; plus `0x81`-lead
full-width symbols `°☆♪…`. ASCII `0x20-0x7E` is itself. Uppercase accented
letters and the rarer accents/ligatures/guillemets have **no confirmed byte**
— the shipped translation folds them to ASCII house-style, and so does
`encode_text`. Still
worth an **emulator spot-check** before bulk reinsertion (no emulator set up
yet), but the table itself is corpus-confirmed (11,264 evet + 465 mcht FR
chunks, zero unmapped letters).

Untranslated entries are separate: they use standard 2-byte Shift-JIS, not
this custom scheme. Always detect per-string which encoding applies (see
`ie3-pkb-pkh-format` / `ie3-str-format` skills for where strings live)
rather than assuming a whole file is one or the other.

## Why this is hard: two failed attempts, know them before trying a third

`tools/collect_french_contexts.py` tries to build a byte→character mapping
by scanning ROM files for high-byte (≥0x80) characters and their
surrounding context, so a human (or Claude, using French vocabulary
knowledge) can pattern-match e.g. `"d{XX}j{YY}"` in a plausible context to
`"déjà"`. Two attempts so far, both too noisy to use:

1. **Scanning every extracted file.** Drowned in noise from huge binary
   formats — `.nsbmd` 3D model files (`BMD0` chunk headers), sound-sequence
   files (MIDI-style `trk ` chunks) — that coincidentally contain
   high-byte + ASCII-letter runs matching the token regex. Fix: restrict to
   a curated list of files known/suspected to hold real text.
2. **Restricting to `.STR`/`.pkb` text files.** Still noisy — turned out to
   be **leftover untranslated Shift-JIS Japanese** in these same
   partially-translated files. Byte `0x82` (the single most common SJIS
   lead byte, covering all hiragana) topped the frequency table at ~294k
   hits. Fix applied: added an SJIS-pair exclusion filter (skip any byte
   position that decodes as part of a valid SJIS lead/trail pair).
3. **Even with the SJIS filter**, still noisy for `.pkb` files that are
   mostly script *bytecode* rather than prose (`mch.pkb`, `act.pkb`,
   `mrobj.pkb`) — raw regex-over-whole-file picks up binary opcode/parameter
   bytes that coincidentally look text-ish (a repeating `0xFF ×8 + "SSD"`
   pattern was one observed false signal — clearly a binary chunk marker,
   not French text).

## The approach to actually take

**Don't regex over whole files.** Use the `.pkh`-bounded slot parser
approach proven in `tools/inspect_pkh2.py` (see the `ie3-pkb-pkh-format`
skill) to extract only properly-delimited, genuine text sub-strings from
`evet.pkb` (and other confirmed *text* pairs — not the bytecode-only `eve`/
`mch`/`act`/`mr`/`mrobj` files, which shouldn't be scanned for prose at
all). Re-run the high-byte context collection only on that cleanly-bounded
text. French has a small closed set of accented characters (à â ä ç é è ê ë
î ï ô ö ù û ü œ æ, uppercase variants, guillemets « », apostrophe variants),
so with clean context this should resolve fairly quickly by pattern-matching
against real French words in context.

**Cross-check candidates against the font.** `data_iz/font/FONT12.NFTR` and
`FONT8.NFTR` ("Nitro Font Resource") have a CMAP block mapping byte/char
codes to glyph indices. This won't tell you *which letter* a glyph is
(needs bitmap rendering), but tells you whether a byte value is even a
valid mapped character code at all — useful for ruling out control codes
vs. real characters. `ndspy` has no built-in NFTR parser; would need to be
written from the binary spec if pursued. Not yet attempted.

**Ultimate validation**: render the ROM in an emulator after writing a test
string with your hypothesized encoding and visually confirm it displays
correctly, before trusting the table for bulk reinsertion. No emulator is
set up in this environment yet.

## When you do get a confirmed mapping

Record it in `docs/FORMAT_NOTES.md` (update the "Custom single-byte French
character encoding — UNSOLVED" section — rename it once it isn't unsolved
anymore) as the source of truth, not just in this skill or in code
comments. Keep this skill's description of the failed attempts around even
after solving it — it's useful context for why the naive approach doesn't
work, in case the mapping ever needs re-deriving (e.g. for a different
game/ROM using the same Level-5 engine family).
