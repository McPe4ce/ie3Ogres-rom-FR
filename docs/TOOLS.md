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

## Not yet built

- A real slot-by-slot extractor for `.pkb`/`.pkh` pairs that outputs
  `(id, sub_index, decoded_text)` for every entry, auto-detecting SJIS vs.
  custom-encoding per entry.
- A `.STR` extractor (once the indexing mechanism is confirmed).
- A reinsertion tool that writes edited/translated strings back into a
  `.pkb`/`.STR` file (and `.pkh` offset table, if any offsets shift) and
  repacks the whole ROM via `ndspy`'s `NintendoDSRom` write support.
- Anything for testing in an emulator (no emulator installed in this
  environment yet; testing has been code/byte-level only so far).
