# Tools

All scripts live in `tools/` and use the venv at `tools/venv/` (Python 3.12
+ [`ndspy`](https://pypi.org/project/ndspy/)). Run from inside `tools/`:

```bash
cd tools
source venv/bin/activate
```

If the venv doesn't exist yet: `python3 -m venv venv && source venv/bin/activate && pip install ndspy`

## `extract_rom.py`

Dumps the entire ROM to `../extracted/`: full filesystem tree under
`data_iz/` and `dwc/`, plus `_arm9.bin`, `_arm7.bin`, and
`_overlay9/overlay9_NNNN.bin` for every ARM9 code overlay. Edit `ROM_PATH`
at the top if the ROM file is moved/renamed.

```bash
python3 extract_rom.py
```

Idempotent — safe to re-run any time (e.g. after re-applying a patched ROM)
to refresh the extracted copy.

## `list_files.py`

Walks the ROM's internal filename table and prints every file path, one per
line, plus the game code/name and total file count. Used to generate
`filelist.txt`.

```bash
python3 list_files.py > filelist.txt
```

## `scan_japanese.py`

Scans every file under `../extracted/` for runs of ≥6 consecutive
Shift-JIS characters that decode to hiragana/katakana/kanji. This is how
the remaining untranslated-text gaps were located. Prints, per file: the
number of runs found and the offset + first ~40 chars of up to 5 sample
runs. Takes a couple minutes over the full 453MB extraction.

```bash
python3 scan_japanese.py > jp_scan_results.txt
```

Remember: hits inside `.SAD` audio files are false positives (see
`docs/FORMAT_NOTES.md`). Treat any hit outside `data_iz/script/*.pkb` /
`data_iz/logic/*.STR` with suspicion.

## `inspect_pkh.py`

One-off structural probe of `evet.pkh` / `evet.pkb`: confirms the magic
string, file-size self-reference, and tries candidate `(header_size,
record_size)` combinations to find one where `(filesize - header) %
record_size == 0`, printing the resulting record count for each candidate.
This is how header=48 bytes / record=12 bytes was identified as the correct
combination (the header's own declared record-count field at `0x16`
matched the count computed from that combination).

```bash
python3 inspect_pkh.py
```

## `inspect_pkh2.py`

Follow-up to `inspect_pkh.py`: parses the first `count` `.pkh` records with
the confirmed 12-byte layout (`ID, offset, budget`), prints them alongside
a naive null-byte-scan of the raw `.pkb` file, and prints deltas between
consecutive records — this is how the ID-stride pattern (steps of 10000)
and the offset/budget relationship were confirmed. Useful as a template for
writing a real slot-by-slot text extractor (not yet built — see
`docs/FORMAT_NOTES.md` "Recommended next approach").

```bash
python3 inspect_pkh2.py
```

## `collect_french_contexts.py`

Attempts to collect surrounding-character context for every high-byte
(≥0x80) character found in a curated list of suspected-text files, to help
manually derive the custom French character encoding table. Excludes bytes
that are part of a valid Shift-JIS kana/kanji pair. **Still too noisy to be
directly useful** — see `docs/FORMAT_NOTES.md` for why (binary bytecode
files pollute the signal) and the recommended fix (restrict to properly
`.pkh`-bounded string slots instead of raw regex over whole files).

```bash
python3 collect_french_contexts.py > french_contexts.txt
```

The `CANDIDATES` list at the top of the file controls which files get
scanned — edit it to narrow/widen scope.

## Format-analysis probes (`.STR` indexing — resolved)

- `analyze_str_dat.py` / `analyze_str_dat2.py` — probe `item.dat`/`unitbase.dat`
  for an offset or index column into their `.STR`. Found none.
- `find_offset_table.py` — **decisive**: searches all extracted files for
  `item.STR`'s offset sequence in any encoding; found nowhere ⇒ ordinal index,
  resizing safe. See `docs/FORMAT_NOTES.md` → `.STR` section.
- `verify_str_align.py` — confirms every `.STR` string is 32-byte aligned and
  classifies JP vs FR (item/unitbase are 100% untranslated Japanese). Re-run
  after any `.STR` edit to check the four safe-editing invariants still hold.

## French encoding derivation (`ie3_codec.py` — solved)

- `ie3_codec.py` — **the codec**. `decode_text(bytes)` / `encode_text(str)`
  for the custom single-byte FR encoding, with `<XX>` control-token round-trip
  and house-style folding of unsupported chars. Has a round-trip self-test
  (`python3 ie3_codec.py`). Import this everywhere; don't re-derive the table.
- `evet_extract.py` — slot→chunk parser + JP/FR/ascii/ctrl classifier for a
  `.pkb`/`.pkh` pair (library `parse_evet(name)` + CLI summary).
- `derive_encoding.py` / `derive_encoding2.py` — how the table was derived
  (high-byte context tally over clean FR chunks). Kept for provenance.

## Text extraction & reinsertion (`.pkb`/`.pkh`)

- `evet_slots.py` — **byte-exact slot model** (`load_slots`, `Slot`). Proven to
  round-trip all evet+mcht slots (`python3 evet_slots.py evet` reports 0
  failures). Editing conserves each slot's budget span, so the `.pkh` never
  needs changing. This is the foundation the dump/reinsert tools sit on.
- `evet_dump.py` — dump translatable text to an editable JSON:
  `python3 evet_dump.py evet [--jp-only] [-o out.json]`. Each entry has a
  read-only `src` (Japanese to translate, or current French) and an editable
  `fr` field. The leading box/speaker control byte is preserved automatically.
- `evet_reinsert.py` — apply the edited JSON back into a **new** `.pkb`
  (original untouched): `python3 evet_reinsert.py trans.json --out evet_new.pkb`.
  Encodes each edited `fr`, re-fits it within the slot's budget, and refuses to
  write if any edit overflows (unless `--allow-overflow`). Reports house-style
  folds. A no-op reinsert reproduces the original `.pkb` byte-for-byte.

Workflow: `evet_dump.py` → edit `fr` fields → `evet_reinsert.py` →
`repack_rom.py` (below) → test in emulator.

## Whole-ROM repack (`repack_rom.py`)

Writes edited internal file(s) back into a **new** `.nds` via `ndspy` (source
ROM never modified). Maps an internal ROM path to a local edited file:

```bash
# pure round-trip: prove the repack is content-lossless
python3 repack_rom.py -o /tmp/roundtrip.nds --verify

# patch one file
python3 repack_rom.py -r data_iz/script/evet.pkb=evet_new.pkb -o patched.nds --verify

# patch several
python3 repack_rom.py -r data_iz/script/evet.pkb=evet_new.pkb \
                      -r data_iz/logic/item.STR=item_new.STR -o patched.nds --verify
```

**Important — the output `.nds` is NOT byte-identical to the source.** `ndspy`
rebuilds the container: it rewrites the file allocation table, relocates files,
and trims the original's trailing padding (~512 MB → ~447 MB). The real
correctness invariant is **content-lossless**: `--verify` re-reads the output
and asserts every internal file, both ARM binaries, and all 133 overlays match
what was packed (edited files carry the edit; all others match the source).
Verified: a one-slot evet edit produces a patched ROM differing from the
original in exactly `data_iz/script/evet.pkb` and nowhere else.

## Text extraction & reinsertion (`.STR`)

Mirror of the `.pkb` pipeline for `data_iz/logic/*.STR` flat string pools.
Lookup is by ordinal index (no offset table), so strings resize freely — no
per-record budget. Built 2026-07-19; round-trips all seven `.STR` files.

- `str_slots.py` — **byte-exact model** (`load`, `parse_str`, `build_str`).
  `python3 str_slots.py item unitbase` runs a round-trip self-test + census.
  Captures each record's *actual* trailing padding (alignment is a per-file
  convention — `games.STR` packs some strings tight; see `FORMAT_NOTES.md`).
- `str_dump.py` — dump translatable records to editable JSON, addressed by
  ordinal `idx`: `python3 str_dump.py item [--jp-only] [-o out.json]`. Empty/
  padding records are skipped but their indices preserved.
- `str_reinsert.py` — apply the edited JSON into a **new** `.STR` (original
  untouched): `python3 str_reinsert.py trans.json --out item_new.STR`. Preserves
  record count/order, re-pads edited records to 0x20, reports house-style folds.
  A no-op reinsert reproduces the original byte-for-byte.

Workflow: `str_dump.py` → edit `fr` fields → `str_reinsert.py` →
`repack_rom.py` → test in emulator.

## Still to build

- Emulator testing (none installed yet) — the encoding itself is effectively
  proven (the shipped v06 patch already renders these bytes in-game; edits use
  only that already-renderable alphabet), so a visual check is now mainly to
  confirm **reflow of newly-sized strings**. Do it on the first real translated
  batch. See `HANDOFF.md`.
