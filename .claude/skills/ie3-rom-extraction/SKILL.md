---
name: ie3-rom-extraction
description: Use when the user wants to extract, re-extract, or refresh this Inazuma Eleven 3 NDS ROM's internal filesystem, list its internal files, or scan it for remaining untranslated Japanese text. Triggers on requests like "extract the rom", "re-dump the rom", "what files are in the rom", "find untranslated text", "scan for japanese text", "check what's still not translated", or after the .nds file at the repo root has changed (e.g. a new patch version applied) and derived data needs refreshing.
---

# IE3 ROM Extraction & Gap Scanning

This project reverse-engineers a French fan translation of *Inazuma Eleven 3*
(NDS) to find and fill in text the existing patch missed. This skill covers
the entry point of that workflow: getting the ROM's internal files onto disk
and locating where untranslated Japanese text remains.

Read `README.md` and `docs/FORMAT_NOTES.md` at the repo root first if you
haven't already — they hold the full picture of what's been learned about
this specific ROM. This skill is just the "how to run the tools" layer.

## Setup

All tooling lives in `tools/`, using a venv at `tools/venv/`:

```bash
cd tools
source venv/bin/activate   # if missing: python3 -m venv venv && pip install ndspy
```

The only dependency is [`ndspy`](https://pypi.org/project/ndspy/), a
pure-Python NDS ROM library. No `ndstool` binary or other external tool is
needed.

## Extracting the ROM filesystem

```bash
python3 extract_rom.py
```

Dumps the ROM (path hardcoded near the top of the script — update it if the
`.nds` filename changes, e.g. a new patch version) to `../extracted/`:
the full `data_iz/` and `dwc/` filesystem tree, plus `_arm9.bin`,
`_arm7.bin`, and `_overlay9/overlay9_NNNN.bin` for each ARM9 code overlay.
Idempotent — safe to re-run any time, e.g. after swapping in a newer patch
version of the ROM to refresh the extracted copy.

`extracted/` is ~450MB and gitignored — never commit it, always regenerate.

## Listing internal files

```bash
python3 list_files.py > filelist.txt
```

Walks the ROM's internal filename table (via `ndspy.rom.NintendoDSRom`) and
prints every path. Useful for spotting new/renamed files if the ROM changes,
or for `grep`-ing for files by extension/keyword when hunting for where a
particular kind of content lives.

## Finding untranslated Japanese text

```bash
python3 scan_japanese.py > jp_scan_results.txt
```

Scans every extracted file for runs of ≥6 consecutive Shift-JIS characters
that decode to hiragana/katakana/kanji. Takes a couple minutes over the full
extraction. Output is ranked by number of runs found per file — the biggest
numbers are the biggest translation gaps.

**Known false positives**: `.SAD` audio files reliably show up with dozens
to hundreds of "hits" that are not real text — audio sample bytes
coincidentally form valid Shift-JIS byte pairs. Ignore hits outside
`data_iz/script/*.pkb`, `data_iz/logic/*.STR`, or other files already
confirmed to hold real text (see `docs/FORMAT_NOTES.md`). When in doubt,
hex-dump the offset and eyeball it before trusting a hit.

As of the last full scan, the confirmed real gaps, ranked by size, are:
`data_iz/script/evet.pkb` (main event/story dialogue — by far the largest),
`data_iz/logic/unitbase.STR` (player roster), `data_iz/logic/item.STR`
(item descriptions), plus smaller hits in `blogpost.dat` and a couple of
menu `.pkb` files. Re-run the scan rather than trusting this list blindly if
significant translation work has happened since — it will drift.

## After finding a gap

Once you know *which* file has untranslated text, hand off to the
format-specific skill:
- `.pkb`/`.pkh` pairs (script/dialogue archives) → see the
  `ie3-pkb-pkh-format` skill.
- `.STR` files (flat string pools) → see the `ie3-str-format` skill.
- Either format, once you have raw bytes to decode/encode → see the
  `ie3-french-encoding` skill for the custom character table.
