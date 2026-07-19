# Inazuma Eleven 3 (Ogre) — French Patch Gap-Fill

Personal, educational reverse-engineering project on a French fan-translation
ROM of *Inazuma Eleven 3: Sekai e no Chousen!! The Ogre* (NDS). The existing
v06 patch is only partially translated — this project's goal is to locate the
remaining untranslated Japanese text, understand the game's internal text
formats well enough to edit them safely, and fill in the gaps.

Scope: personal copy, personal/learning use. Not for redistribution.

## Status (as of this writing)

| Step | Status |
|---|---|
| Extract ROM filesystem | ✅ done |
| Locate remaining Japanese text | ✅ done |
| Reverse-engineer `.pkb`/`.pkh` script-text format | ✅ done (see [`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md)) |
| Reverse-engineer custom French character encoding | ✅ done — `tools/ie3_codec.py` (see [`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md)) |
| Reverse-engineer `.STR` flat string pool format | ✅ done — ordinal index, resizing safe (see [`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md)) |
| Build extraction script (dump text + IDs to editable file) | ✅ done — `.pkb`: `tools/evet_dump.py`; `.STR`: `tools/str_dump.py` |
| Build reinsertion script (write translations back) | ✅ done — `.pkb`: `tools/evet_reinsert.py` (budget-checked); `.STR`: `tools/str_reinsert.py` (resize-free); both byte-exact round-trip |
| Whole-ROM repack (edited files → new `.nds`) | ✅ done — `tools/repack_rom.py`, content-lossless (`--verify`); one-slot edit proven to land in the ROM |
| Test in emulator | ⬜ not started (no emulator yet) |
| Draft French for the 15,756 `evet` Japanese chunks | ⬜ awaiting translator (Phil) — extraction is ready |

## Quickstart

```bash
cd tools
source venv/bin/activate   # python3 -m venv venv && pip install ndspy, if missing
python3 extract_rom.py     # dumps ROM filesystem to ../extracted/
python3 scan_japanese.py   # finds remaining Japanese text, writes jp_scan_results.txt
```

The ROM itself lives at the repo root:
`Inazuma-Eleven-3-Sekai-heno-Chousen-The-Ogre-DS-Traduit-en-Français-v06.nds`

`extracted/` (453MB, ROM filesystem dump) and `tools/venv/` are git-ignored —
regenerate with `extract_rom.py` rather than committing them.

## Where the untranslated text is

Found via `tools/scan_japanese.py` (Shift-JIS run detection across all
extracted files — see [`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md#locating-untranslated-text)
for method and caveats). Ranked by volume:

1. **`data_iz/script/evet.pkb`** — 22,672 runs. Main event/story dialogue text. The big one.
2. **`data_iz/logic/unitbase.STR`** — 3,144 runs. Player roster names/stats.
3. **`data_iz/logic/item.STR`** — 509 runs. Item descriptions.
4. Smaller gap: `data_iz/script/blogpost.dat`, `_overlay9_0004.bin`.

`.SAD` sound files show up in the scan but are false positives (binary audio
matching Shift-JIS by coincidence). So do the menu `.pkb`s
(`data_iz/pic2d/cmd/mbd_c.pkb`, `tcd_c.pkb`) — those are **tile/graphics data**
(repeating `0x77`/`0x7C`/`0xFF` patterns), not text; ignore them.

## Status of the former blockers (both resolved)

- **Custom character encoding — SOLVED.** The 11 lowercase accented letters
  (`0xC9`ù, `0xB1`à, …) plus `0x81`-lead symbols were derived from cleanly
  `.pkh`-bounded French chunks and implemented in `tools/ie3_codec.py`.
- **`.STR` indexing — SOLVED.** Ordinal index (no offset table exists
  anywhere), so `.STR` strings can be resized freely under four invariants.

Extraction + reinsertion for `.pkb` dialogue is built and byte-exact
(`tools/evet_dump.py` / `tools/evet_reinsert.py`). Remaining work: `.STR`
dump/reinsert tools, whole-ROM repack via `ndspy`, and emulator validation.

New to this / want the intuition first? Read
[`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md) — a plain-language explainer with
diagrams. Then [`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md) for full technical
detail and [`docs/TOOLS.md`](docs/TOOLS.md) for what each script does.

## Claude Code skills

`.claude/skills/` has four project-scoped skills that capture this
project's tooling and reverse-engineered format knowledge, so a fresh
Claude Code session doesn't have to re-derive it. They auto-trigger based
on what you're working on, or can be read directly:

- `ie3-rom-extraction` — extracting the ROM and scanning for untranslated text
- `ie3-pkb-pkh-format` — the `.pkb`/`.pkh` "PackNum" script/dialogue archive format
- `ie3-str-format` — the `.STR` flat string pool format
- `ie3-french-encoding` — the (unsolved) custom French character encoding, and what not to try again

Keep these in sync with `docs/FORMAT_NOTES.md` as the format understanding
evolves — the docs are the source of truth, the skills are a condensed,
task-oriented pointer to them.
