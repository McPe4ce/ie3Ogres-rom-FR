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
| Reverse-engineer custom French character encoding | 🔶 in progress, blocked — see "Known blockers" below |
| Reverse-engineer `.STR` flat string pool format | ⬜ not started |
| Build extraction script (dump text + IDs to editable file) | ⬜ not started |
| Build reinsertion script (write translations back into ROM) | ⬜ not started |
| Repack + test in emulator | ⬜ not started |

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
4. Smaller gaps: `data_iz/script/blogpost.dat`, a few menu `.pkb` files
   (`data_iz/pic2d/cmd/mbd_c.pkb`, `tcd_c.pkb`), `_overlay9_0004.bin`.

`.SAD` sound files also show up in the scan but are false positives — binary
audio data coincidentally matching Shift-JIS byte patterns, not real text.

## Known blockers

**Custom character encoding not yet solved.** The existing French text does
not use standard Latin-1/CP1252 — e.g. byte `0xC9` renders as `ù`, not `É`.
We need the full byte→character table before new French text can be written
back safely. Two attempts documented in `docs/FORMAT_NOTES.md`; both were too
noisy because several `.pkb` files (`mch.pkb`, `act.pkb`, `mrobj.pkb`, etc.)
are mostly script bytecode, not text, and pollute a naive whole-file scan.
**Next step**: restrict the context-collection scan to properly
`.pkh`-bounded, null-terminated string slots only (the parsing approach
proven in `tools/inspect_pkh2.py`), not raw regex over whole files.

See [`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md) for full technical detail
and [`docs/TOOLS.md`](docs/TOOLS.md) for what each script does.

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
