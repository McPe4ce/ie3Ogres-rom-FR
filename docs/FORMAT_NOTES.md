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

## Custom single-byte French character encoding — SOLVED (2026-07-18)

Derived empirically from cleanly `.pkh`-bounded evet French chunks (11,264)
and cross-checked against mcht (465) — both genuine dialogue archives use the
**identical** accented-letter set, and decoding all 11,264 evet French chunks
leaves **zero** unmapped high bytes (only sub-`0x20` inline control codes
remain, which are correctly opaque). Implemented in `tools/ie3_codec.py`
(`decode_text` / `encode_text`, with a round-trip self-test). Tools used to
derive it: `evet_extract.py` (slot→chunk parser + JP/FR/ascii/ctrl
classifier), `derive_encoding.py`, `derive_encoding2.py`.

### Confirmed byte → character table

Base: bytes `0x20..0x7E` are **standard ASCII**; `0x0A` is newline. The
custom accented letters (single byte each):

| byte | char | byte | char | byte | char |
|------|------|------|------|------|------|
| 0xB1 | à    | 0xBA | é    | 0xC0 | ï    |
| 0xB3 | â    | 0xBB | ê    | 0xC5 | ô    |
| 0xB8 | ç    | 0xBF | î    | 0xC9 | ù    |
| 0xB9 | è    | 0xCB | û    |      |      |

All eleven are **lowercase** accented letters (e.g. `0xC9`ù appears in
"Où veux-tu aller?" — capital O + lowercase ù, not an all-caps "OÙ").

Two-byte **full-width SJIS symbols** embedded in French text (lead `0x81`):
`0x81 0x8B` = `°`, `0x81 0x99` = `☆`, `0x81 0xF4` = `♪`, `0x81 0x63` = `…`.
Preserve these verbatim.

### What this translation does NOT use (house style)

Across 11,729 real French chunks **no uppercase accented letters appear at
all** — every accent byte is lowercase. Sentence-initial capitals are written
**unaccented** ("A cette époque", "Equipe"), and the rarer accents (ë ö ü œ æ)
and
guillemets « » do not appear — the translators used ASCII `oe`/`ae`/straight
quotes. The font (`FONT12.NFTR`) very likely *has* glyphs for these, but no
byte assignment is confirmed for them, so `ie3_codec.encode_text` folds them
to house-style ASCII (recording each fold) rather than guessing a byte. If a
future need arises for real É/È/À/œ bytes, parse the NFTR CMAP to recover the
full glyph table (not yet done).

### Control codes (preserve verbatim, never translate)

- **Position-0 byte of every sub-string** = an opaque box/speaker/style
  control code. Observed values are all multiples of 4 (`0x80,0x84,…,0xD4`,
  and ASCII ones like `<` `d` `,` `4` `(`).
- **Inline** standalone low bytes `0x04, 0x10, 0x14, 0x18, 0x1C` = in-text
  control codes (text speed/pause/color, unconfirmed exact meaning). Keep as
  opaque bytes.

### Historical note (why naive scans failed — see also the skill)

Byte `0xC9` is `ù` (u-grave) and `0xB1` is `à` — NOT CP1252 (`É`/`±`). Prior
whole-file frequency scans drowned in SJIS-leftover and bytecode noise; the
fix was restricting to `.pkh`-bounded, null-terminated, FR-classified chunks
of the *text* archives (evet/mcht) only, never the bytecode files
(eve/mch/act/mr/mrobj) or the tile-data menu `.pkb`s (mbd_c/tcd_c), both of
which produce all-high-byte false positives.

### How it was finally solved (the approach that worked)

The three earlier failed attempts (`tools/collect_french_contexts.py` — kept
for reference) all regex'd over whole files and drowned in noise: `.nsbmd`
model/`.ssar` sound chunks, then leftover SJIS Japanese (byte `0x82` topped
at ~294k hits), then bytecode opcode bytes from `mch`/`act`/`mrobj`. The fix
that worked: **don't scan whole files** — parse `.pkh`-bounded slots, split
into null-terminated sub-strings, classify each (JP / FR / ascii / ctrl by
double-byte-SJIS coverage), and tally high bytes **only** in FR chunks of the
real text archives (evet, mcht). With that clean signal every accented byte
was read straight off the surrounding French word (`exp<BA>rience` → é, etc.)
and the whole table fell out in one pass. `FONT12.NFTR` CMAP cross-checking
was noted as a fallback but proved unnecessary for the letters actually used.

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

**RESOLVED (2026-07-18): lookup is by ORDINAL INDEX, not byte offset —
resizing is safe.** Investigated with `tools/analyze_str_dat.py`,
`analyze_str_dat2.py`, and the decisive `tools/find_offset_table.py`:

- `item.dat` (45,056 B) is dense bit/byte-packed binary (0xAD filler),
  **not** a clean fixed-record table. It contains **zero** plaintext u32
  byte-offsets into `item.STR` (raw u32 match count = 0), and no monotonic
  offset/index column at any tested record size. `unitbase.dat` likewise has
  no structured offset column (its scattered u16/u32 "matches" are dense-
  binary coincidences).
- Decisive check: `find_offset_table.py` computed `item.STR`'s exact
  string-start offset sequence and searched **all 1,987 extracted files**
  for it as consecutive u32/u16 raw offsets, as `offset>>5` block indices,
  and as u16 length-deltas. **No offset/length table exists anywhere in the
  extraction.** Hardcoding 822 offsets as code immediates is implausible, so
  the loader necessarily locates the Nth string by counting null terminators
  at load time — i.e. ordinal indexing.

**Editing rule (safe):** a `.STR` file may be freely re-translated, resizing
strings up or down, **provided** you preserve: (1) the total record count,
(2) the record order, and (3) one `0x00` terminator per record. Do **not** add
or remove strings/terminators. There is **no per-record byte budget** — ordinal
lookup means absolute offsets don't matter.

**CORRECTION (2026-07-19): 32-byte alignment is a per-file CONVENTION, not a
universal invariant.** The earlier claim that every string is 0x20-aligned holds
only for the fully-Japanese files (`item`, `unitbase`, `command`). A byte-exact
model over **all seven** `.STR` files (`tools/str_slots.py`) revealed that
`games.STR` (partially French) **packs some strings tight** — a French string
begins immediately after the previous terminator with no alignment padding. So
alignment must be *captured per record*, not assumed. `str_slots.py` records the
actual padding and round-trips all seven files byte-for-byte. `item`/`command`
are exactly **1024-record fixed tables** (used strings + empty padding records),
which further supports ordinal indexing. (`games.STR` also uses UTF-8 for a few
punctuation marks like `°` — detect encoding per-string.)

`item.STR` (822 strings) and `unitbase.STR` (2374 strings) are currently **100%
untranslated Japanese SJIS**, so every entry is fair game.

**Encoding — `.STR` is FULL-WIDTH SJIS, not the single-byte dialogue encoding
(confirmed 2026-07-19).** Translated `.STR` text (menus, item/player
descriptions) is written in **full-width SJIS Latin with NO accents** — letters
are full-width forms (`0x82 xx`), space is the full-width space `　` (`0x81 40`),
apostrophe is `’` (`0x81 66`), accented letters are written unaccented (house
style). This is a **different encoding** from `evet.pkb` dialogue (single-byte,
lowercase-accented — `tools/ie3_codec.py`). Verified: the shipped already-French
`.STR` pools (`sp_binder`, `command`, `tacticscmd`) contain **zero**
single-byte-accent bytes, and `tools/str_codec.py` (`encode_str_fr` /
`decode_str_fr`) reproduces 1206/1207 of them byte-exactly (the 1 is a
blank-spaces record). Use `str_codec` for `.STR`; never `ie3_codec`.

**Tooling (built 2026-07-19):** `tools/str_slots.py` (byte-exact model +
round-trip self-test), `tools/str_codec.py` (full-width FR codec), `str_dump.py`
(dump translatable records to JSON, addressed by ordinal `idx`),
`str_reinsert.py` (apply edits into a new `.STR`, count/order preserved, edited
records re-padded to 0x20, no budget check). Feed the result to
`tools/repack_rom.py`. A no-op reinsert reproduces the original byte-for-byte.
See `docs/TOOLS.md`. **Translation status:** `item.STR` 448/822 in
`translations/item.json`; see the `ie3-translation` skill + `docs/NAME_GLOSSARY.md`.

## Open questions / TODO

- [x] ~~Derive the custom single-byte→character encoding table.~~ **SOLVED
      2026-07-18** — see the encoding section above / `tools/ie3_codec.py`.
- [x] ~~Determine `.STR` file indexing mechanism.~~ **SOLVED 2026-07-18** —
      ordinal index, resizing safe (see `.STR` section above).
- [x] ~~Confirm the `.pkh`/`.pkb` format generalizes beyond evet.~~ **mcht
      confirmed** — `evet_extract.parse_evet("mcht")` parses cleanly and its
      465 French chunks use the identical encoding. (`help.pkb` is tiny/mostly
      non-text; the bytecode siblings eve/mch/act/mr/mrobj are not prose.)
- [ ] Determine meaning of `.pkh` header fields at `0x14` (u16) and `0x18`/
      `0x1C` (u32×2) — currently unexplained. (Not needed for text editing.)
- [ ] Confirm whether `eve.pkb` bytecode references `evet.pkb` text by the ID
      field vs. within-slot sub-string index — matters for how safely
      sub-strings inside one slot can be reflowed/resized during reinsertion.
      Would need to disassemble `eve.pkb` around a known dialogue trigger.
- [ ] Exact meaning of inline control codes (leading box code per sub-string;
      inline `0x04/0x10/0x14/0x18/0x1C`). Preserved verbatim regardless, but
      knowing them would help validate reinsertion in an emulator.
- [ ] **Furigana-ruby chunks in evet slots (found 2026-07-23, rec 975).** Some
      NPC/tutorial slots hold one big `\f`-paginated SJIS dialogue chunk
      followed by a tail of short pure-hiragana chunks that are **ruby
      readings** of the kanji words in the main chunk, in order of appearance
      (rec 975: p1–p9 = じっしゅうしつ・てんすう・わる・ほしゅう・う・てん・
      わる・ほしゅう・べんきょう ↔ 実習室/点数/悪/補習/受/点/悪/補習/勉強 in
      p0). Hex-dump confirms the main chunk has **no inline ruby markers**
      (kanji flow directly in SJIS), so the text↔ruby association must live in
      the `eve.pkb` event bytecode (ties into the ID-vs-index question above).
      Unknown whether replacing the main chunk with French (no kanji) orphans
      the ruby cleanly or paints stray kana over the box. **Until one such rec
      is emulator-tested, defer these recs entirely** (975 is excluded in the
      HANDOFF queue script) and never translate the kana tails as content.
      Contrast: rec 46/47's lone `れんしゅう` chunk was a real menu label
      (translated "Entraînement"), not ruby — the tell for ruby is the ordered
      correspondence with the kanji of a neighbouring big chunk.
