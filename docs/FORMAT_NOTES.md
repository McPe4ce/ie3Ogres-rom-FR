# Format Notes

Technical findings from reverse-engineering the ROM. This is a living
document — update it as new format details are confirmed.

## ROM overview

- Engine: Level-5's DS engine (same family as Professor Layton).
- Game code: `BOEJ` ("INAZUMA11"), region JP, this copy already has a
  partial (v06) French fan patch applied ("decrypted" per `file(1)`, so it's
  a raw ROM image, not an encrypted retail dump).
- Filesystem root of interest: `data_iz/` — everything gameplay-relevant
  lives under here (scripts, logic tables, fonts, sound, models).
- Extracted via [`ndspy`](https://pypi.org/project/ndspy/), a pure-Python
  NDS ROM library — handles the NitroROM filesystem, NARC archives, and
  overlay loading. No `ndstool` binary needed.
- `tools/extract_rom.py` also dumps `arm9`/`arm7` binaries and all ARM9
  overlays, since some games keep pointer tables or embedded strings in code
  rather than the filesystem — not yet needed, but there if required later.

## Locating untranslated text

`tools/scan_japanese.py` walks every extracted file and looks for runs of
valid Shift-JIS byte pairs that decode to hiragana/katakana/kanji (Unicode
ranges `U+3040–30FF`, `U+4E00–9FFF`, halfwidth kana `U+FF66–FF9D`). A "run"
is only reported if it's ≥6 consecutive Japanese characters, to cut down on
incidental noise from binary data that happens to contain a valid SJIS pair
or two.

**Caveat**: this still produces false positives on binary formats where byte
values coincidentally form valid SJIS pairs — this is very common in `.SAD`
audio files, which show up with hundreds of "runs" that are not real text.
Treat any hit outside of `data_iz/script/*.pkb`, `data_iz/logic/*.STR`, or
similar known text-container formats with suspicion; verify with a hex dump
before trusting it.

## The `.pkb` / `.pkh` format ("PackNum")

Used for script/dialogue text: `data_iz/script/{eve,evet,mch,mcht,help,act,
mr,mrobj}.{pkb,pkh}`, and also `data_iz/pic2d/cmd/*.pkb` (menu commands),
`data_iz/effect3d/eff.pkb`, `data_iz/model/*/*.pkb`, etc. — this is a
general-purpose Level-5 archive format, not text-specific; `eve.pkb` (no
`t`) is believed to hold event *script/bytecode* (flow control) while
`evet.pkb` holds the *text* that bytecode references by ID. Same pattern for
`mch`/`mcht`.

### `.pkh` (header/index file)

Confirmed via `tools/inspect_pkh.py` / `inspect_pkh2.py` against
`data_iz/script/evet.pkh` (35,712 bytes) cross-checked against its paired
`evet.pkb` (2,926,480 bytes):

```
Offset  Size  Field
0x00    16    Magic string "PackNum 20080626" (ASCII, no null terminator needed — exactly 16 bytes)
0x10    4     u32 LE — total file size of this .pkh file (self-referential; verified equal to len(file))
0x14    2     u16 LE — unknown, observed value 1 (version/flags?)
0x16    2     u16 LE — record count (verified: 2972 for evet.pkh; (filesize - 48) / 12 == this value)
0x18    4     u32 LE — unknown, observed value 16 (NOT the record size — record size is 12; meaning unconfirmed)
0x1C    4     u32 LE — unknown, observed value 0x27D0 (10192) — meaning unconfirmed
0x20    16    reserved/zero padding
0x30    ...   record table, one 12-byte record per entry, `record_count` records
```

Each 12-byte record:

```
Offset  Size  Field
+0x0    4     u32 LE — ID. Observed to increase in clean arithmetic steps
                        (e.g. 31010000, 31020000, 31030000, ... stride 10000)
                        — this looks like a deliberate ID scheme
                        (event_id * 10000 + line_index, or similar), NOT
                        a hash. Likely how eve.pkb bytecode references a
                        specific line of dialogue.
+0x4    4     u32 LE — byte offset into the paired .pkb file where this
                        entry's data starts. CONFIRMED by direct read: at
                        offset 0 for record 0, the .pkb bytes decode to
                        real French dialogue text (see below).
+0x8    4     u32 LE — byte budget: max size in bytes of this slot in the
                        .pkb file. Observed values vary per record (372
                        for the first 12 records in evet.pkh, then jumps to
                        2940, 528, 708, ... for later records — budget size
                        is NOT fixed globally, it varies per entry, probably
                        sized to fit the original Japanese text plus margin).
```

**Practical implication**: entries are referenced by ID (field 1), not by
raw byte offset baked into the referencing bytecode. This strongly suggests
translated text can be freely resized *within its slot's byte budget*
without needing to patch `eve.pkb`'s script logic — the indirection layer
already exists. This has **not yet been proven** by observing `eve.pkb`
bytecode directly; it's an inference from the ID/offset/budget record shape
and should be verified before relying on it for large text expansions.

### `.pkb` (body/blob file)

No file-level header observed (data starts immediately at byte 0). Content
is a sequence of slots, one per `.pkh` record, at the record's declared
offset, each slot up to `budget` bytes long.

**Slot internal structure** (confirmed by hex-dumping the first 372-byte
slot of `evet.pkb`, see `tools/inspect_pkh2.py` output): a slot can pack
*multiple* related sub-strings (e.g. all the options of one dialogue choice
menu), not just one string. Each sub-string looks like:

```
[3 bytes: 0x00 0x00 0x00]  [text bytes, may include control bytes]  [0x00 terminator]
```

- After a sub-string's terminator, the next sub-string starts after a short
  run of zero-padding (not necessarily aligned to any fixed boundary).
- Standalone single bytes like `0x04` appear between/within sub-strings and
  are believed to be in-text control/formatting codes (text speed? choice
  marker? unconfirmed) — treat as opaque bytes to preserve verbatim, not as
  translatable content.
- Example decoded slot 0 of `evet.pkb` (already-translated French; leading
  space is literal, part of the string): `" OÙ veux-tu aller? "`, followed by
  further sub-strings `"<Aller à la carte? "`, `"dPasser par ici?\nCe n'est
  pas ouvert."`, `",Aller au sous-sol?"`, `"4Or, il semble que ce soit
  pour..."`, `"(Ne paye pas de mine"` — the single leading character of each
  (`<`, `d`, `,`, `4`, `(`) is suspected to be a control code (UI icon/box
  style?) rather than a literal first letter, since it doesn't match the
  rest of the sentence grammatically. **Unconfirmed — needs verification**,
  e.g. by finding entries where the leading byte is unambiguously a normal
  letter vs. clearly a control code (compare against font glyph count / test
  in an emulator).
- Untranslated Japanese entries use 2-byte Shift-JIS instead of this
  single-byte scheme — text encoding must be auto-detected per entry (SJIS
  vs. custom single-byte) when extracting/reinserting.

## Custom single-byte French character encoding — UNSOLVED

The already-translated French text does **not** use standard CP1252/Latin-1.
Confirmed example: byte `0xC9` renders as `ù` (not `É` as in CP1252), byte
`0xB1` renders as `à` (not `±`). No table file has been found in the ROM or
repo — it must be derived empirically or from the font.

### Attempts so far (`tools/collect_french_contexts.py`)

1. **First attempt**: scanned every extracted file for high-byte (≥0x80)
   character contexts. Result: dominated by noise from large binary formats
   (`.nsbmd` models with `BMD0` chunks, MIDI-style `.ssar`/sound sequence
   data with `trk ` chunks). Fixed by restricting to a curated list of
   known/suspected text files.
2. **Second attempt**: restricted to `.STR` files and `.pkb` files under
   `data_iz/script/` and `data_iz/pic2d/cmd/`. Result: still dominated by
   noise — turned out to be **leftover untranslated Shift-JIS Japanese**
   still present in these same (partially-translated) files. Byte `0x82`
   (the single most common SJIS lead byte, covering all hiragana) topped
   the frequency table at ~294k hits.
3. **Third attempt**: added an SJIS-pair exclusion filter (skip any byte
   position that's part of a valid SJIS lead/trail pair decoding to
   kana/kanji) before tallying high-byte contexts. Improved but **still
   noisy** — files like `mch.pkb`, `act.pkb`, `mrobj.pkb` are mostly script
   *bytecode*, not text, so raw regex-over-whole-file still picks up binary
   opcode/parameter bytes that coincidentally look text-ish (e.g. a repeating
   `0xFF ×8 + "SSD"` pattern that is clearly a binary chunk marker, not
   French text).

### Recommended next approach

Don't regex over whole files. Instead:

1. Extend the `.pkh`-record parser proven in `tools/inspect_pkh2.py` into a
   full slot walker for `evet.pkh`/`evet.pkb` (and ideally `mcht`, `help`,
   the other confirmed *text* pairs — **not** the bytecode-only `eve`/`mch`/
   `act`/`mr`/`mrobj` files, which shouldn't be scanned for prose at all).
2. Within each slot, parse using the `[00 00 00][text][00]` sub-string
   structure documented above, so only genuine bounded text content is
   collected — this avoids both binary-bytecode noise and stale
   leftover-bytes-past-the-terminator noise.
3. Re-run the high-byte context collection only on that cleanly-extracted
   text. French has a small closed set of accented characters (à â ä ç é è
   ê ë î ï ô ö ù û ü œ æ + uppercase + « » ' etc.), so with clean context a
   human (or the assistant, using French vocabulary knowledge) should be
   able to assign each byte value fairly quickly — e.g. "d{XX}j{YY}" in a
   greeting context is almost certainly "déjà".
4. Cross-check candidate mappings against `data_iz/font/FONT12.NFTR` (and
   `FONT8.NFTR`) — NFTR is "Nitro Font Resource"; it has a CMAP block that
   maps byte/character codes to glyph indices. It won't tell you *which*
   letter a glyph is (that requires rendering the bitmap), but it will tell
   you whether a given byte value is even a valid/mapped character code at
   all, which helps rule out control codes vs. real characters. Not yet
   attempted — `ndspy` doesn't have a built-in NFTR parser, would need to be
   written from the NFTR binary spec (documented in various DS romhacking
   community references).

## `.STR` flat string pool format

Used for simpler tabular text: `data_iz/logic/{command,games,item,rpgtitle,
sp_binder,tacticscmd,unitbase}.STR`.

Confirmed via hex dump of `item.STR` (`tools/inspect_pkh.py`-style manual
inspection, not yet scripted into a standalone tool):

- No file header. Content is a sequence of null-terminated Shift-JIS (or,
  for translated entries, presumably the same custom single-byte encoding)
  strings, concatenated directly.
- Each string starts at a **32-byte-aligned offset** (i.e. after a string's
  null terminator, zero-padding fills up to the next multiple of 0x20
  before the next string begins). Confirmed across the first 15 entries of
  `item.STR` — offsets 0x20, 0x60, 0xA0, 0x100, 0x1E0, 0x240, ... are all
  multiples of 0x20, with variable gaps (not fixed-size slots — a string
  needing more than one 32-byte block simply spans multiple blocks).
- Text includes inline furigana-style annotations for kanji, e.g.
  `[水/みず]` (kanji `/` reading, in brackets) — this is likely a markup
  convention the game's text renderer strips/formats specially, not literal
  bracket characters to preserve as-is when translating (French text
  wouldn't need furigana, but need to confirm the renderer doesn't choke on
  their absence).

**Not yet determined**: how entries in a `.STR` file are looked up/indexed
by the game. `item.dat` exists alongside `item.STR` and is presumed to hold
structured records (price, stats, sprite ID, etc.) that likely also
reference the description text somehow — need to check whether that
reference is a byte offset into `item.STR` (in which case resizing a string
would require also patching `item.dat`'s offset table) or a simple
sequential index (in which case the game may just count null terminators at
load time, and resizing is safe as long as string *order* and *count* is
preserved). This directly determines how safely `item.STR`/`unitbase.STR`
can be edited — **investigate before touching either file**.

## Open questions / TODO

- [ ] Determine meaning of `.pkh` header fields at `0x14` (u16) and `0x18`/
      `0x1C` (u32×2) — currently unexplained.
- [ ] Determine meaning of the single-byte control codes seen at the start
      of `.pkb` sub-strings (`<`, `,`, `4`, `(`, `0x04`, etc.) — control
      codes vs. literal characters.
- [ ] Confirm whether `eve.pkb` bytecode really does reference `evet.pkb`
      text by the ID field (record field 1) rather than a raw offset —
      would need to disassemble a snippet of `eve.pkb` around a known
      dialogue trigger.
- [ ] Derive the full custom single-byte→character encoding table (see
      "Recommended next approach" above).
- [ ] Determine `.STR` file indexing mechanism (see previous section).
- [ ] Repeat the `.pkh`/`.pkb` structural analysis for `mcht.pkb`/`.pkh`
      and `help.pkb`/`.pkh` to confirm the format generalizes (currently
      only verified against `evet.pkh`/`evet.pkb`).
