# Handoff — current state

Quick orientation for the next session. Full detail is in
[`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md) (source of truth) and the four
skills in `.claude/skills/`. Read [`README.md`](README.md) first.

## Where we are (2026-07-19)

All tooling is **built & verified end-to-end** (extract → edit → reinsert →
whole-ROM repack, byte-checked for both text formats), and **translation is
underway** — the project is now in the content-filling phase.

| Thing | State |
|---|---|
| `.STR` indexing (offset vs index) | ✅ **ordinal index** — resizing safe (no offset table exists anywhere). |
| Custom encodings | ✅ **two**: `evet.pkb` dialogue = single-byte accented (`tools/ie3_codec.py`); `*.STR` menus = **full-width SJIS, no accents** (`tools/str_codec.py`, round-trips 1206/1207 shipped-FR records). Don't mix them up. |
| `.pkb`/`.pkh` slot model | ✅ **byte-exact round-trip** on all 2972 evet + 28 mcht slots. |
| `.pkb` extract → edit → reinsert | ✅ **built & tested** (`evet_dump.py` / `evet_reinsert.py`). |
| Whole-ROM repack (edited file → new `.nds`) | ✅ **built & verified** (`repack_rom.py`) — content-lossless; edits land in the ROM, only edited files differ. |
| `.STR` dump/reinsert tools | ✅ **built & verified** (`str_slots/str_dump/str_reinsert/str_codec.py`) — byte-exact on all 7 `.STR` files. |
| Translation house style + skill | ✅ `ie3-translation` skill + `docs/NAME_GLOSSARY.md` (official EU names). |
| **Translating the text** | 🔶 **in progress** — `item.STR` **448/822** done (`translations/item.json`). |
| Emulator test | ⬜ not started (no emulator installed). |

## Translation progress & how to resume (start here tomorrow)

- **Read the `ie3-translation` skill first** — it has the house style, the
  two-encoding rule, terminology, and the per-format workflow.
- **`item.STR`: 448/822 done**, saved in `translations/item.json` (the durable
  artifact — the scratchpad `.nds`/`.STR` builds are gone, but this JSON isn't).
  Rebuild the patched file anytime:
  ```bash
  python3 str_reinsert.py ../translations/item.json --out item_new.STR
  python3 repack_rom.py -r data_iz/logic/item.STR=item_new.STR -o patched.nds --verify
  ```
  Done so far: consumables, travel/route tickets, spirit emblems, story/key
  items, command/skill effect strings, and **all 352 技の秘伝書 technique
  manuals** (done by formula — see the skill).
- **Remaining item.STR (374):** flavour gear — uniforms, spikes, gloves,
  misangas/pendants, formations, GK-shoe names — all reference **team &
  character names**. **Next step: build the team-name glossary** (mine the
  ROM's existing FR + official EU names) and finish the gear with it; that same
  glossary is what `unitbase.STR` (2374 bios) and `evet` dialogue need next.
- **Naming decision (locked):** official European (English-dub) names, kept
  constant — see `docs/NAME_GLOSSARY.md`. Romaji only for truly unknown NPCs.
- **Uncommitted at end of 2026-07-19** (Phil commits himself): new
  `tools/str_codec.py`, `.claude/skills/ie3-translation/`, `docs/NAME_GLOSSARY.md`,
  `translations/`; modified `tools/str_reinsert.py` (encoder fix — the previously
  committed version used the WRONG encoder), `str_dump.py`, `str_slots.py`.

## The pipeline (use these; don't rewrite)

Run from `tools/` with the venv active (`source venv/bin/activate`):

```bash
python3 evet_dump.py evet --jp-only -o evet_jp.json   # extract 15,756 untranslated JP chunks
#  ... edit the "fr" field of each entry in evet_jp.json ...
python3 evet_reinsert.py evet_jp.json --out evet_new.pkb   # writes a NEW .pkb, original untouched
```

- `ie3_codec.py` — the French text codec (`decode_text` / `encode_text`). Run
  it directly for a round-trip self-test. **Import it; never re-derive the table.**
- `evet_slots.py` — byte-exact slot model (`load_slots`, `Slot`). Run directly
  to re-prove round-trip (0 failures expected).
- `evet_dump.py` / `evet_reinsert.py` — extract / reinsert. A no-op reinsert
  reproduces the original `.pkb` byte-for-byte (that's the correctness check).
- `evet_extract.py` — lower-level slot→chunk parser + classifier (imported by
  the above; also runnable for inspection).

One-shot probes kept for provenance (not routine use): `analyze_str_dat*.py`,
`find_offset_table.py`, `verify_str_align.py`, `derive_encoding*.py`.

## Must-know gotchas before touching the code

- **A slot owns exactly `budget` bytes** at its `.pkh` offset. The gap to the
  next record is `04 FF FF…` inter-slot filler — NOT part of the slot.
- **Every sub-string's first byte is a control code** (box/speaker style,
  always a multiple of 4). `evet_dump` strips it into the `lead` field and
  `evet_reinsert` re-attaches it automatically — the editable `fr` text should
  NOT include it.
- **Translations must fit the slot budget.** French is often longer than the
  compact Japanese; `evet_reinsert` refuses to write and lists overflowing
  slots so you can shorten them. Slack comes from the slot's zero-padding.
- **Encoding is lowercase-accents only.** This translation uses no uppercase
  accented letters; `encode_text` folds uppercase accents / `ë ö ü œ æ` / `« »`
  to ASCII house-style and reports each fold. If real uppercase-accent bytes
  are ever needed, parse `data_iz/font/FONT12.NFTR`'s CMAP (not yet done).

## Recommended next steps (roughly in order)

1. ~~**Whole-ROM repack via `ndspy`**~~ ✅ **done** — `tools/repack_rom.py`.
   Use it: `python3 repack_rom.py -r data_iz/script/evet.pkb=evet_new.pkb -o
   patched.nds --verify`. Output is content-lossless but **not** byte-identical
   to the source (ndspy rebuilds the FAT + trims padding, ~512→~447 MB); the
   `--verify` content check is the correctness proof, not a byte diff.
2. **Emulator visual spot-check** — still owed, but lower-priority than first
   thought. Rationale: the shipped v06 patch *already renders* its 11,264
   French chunks in-game, and `ie3_codec` writes only bytes drawn from that
   exact already-renderable alphabet (verified: every byte of a test edit,
   incl. `ù`=`0xC9`, already appears in shipped FR text — zero novel bytes).
   So the *encoding* is effectively proven; what a screen would still confirm
   is **reflow of newly-sized strings** (French longer than the Japanese it
   replaces). Do the visual check on the **first real translated batch**, not
   on the mechanism. A one-slot `Où tester? ù` test build exists but its slot
   (`rec 0`, a travel menu) is hard to reach in-game.
3. ~~**`.STR` dump/reinsert tools**~~ ✅ **done** — `str_slots.py` /
   `str_dump.py` / `str_reinsert.py`, byte-exact on all 7 `.STR` files.
   Correction learned while building: 32-byte alignment is a *per-file
   convention*, not universal (`games.STR` packs some strings tight), so the
   model captures actual padding. Workflow: `str_dump.py item --jp-only` → edit
   `fr` → `str_reinsert.py` → `repack_rom.py -r data_iz/logic/item.STR=…`.

With extraction, reinsertion, and repack all built for both text formats, the
project is **tooling-complete for translation**: the remaining work is the
actual French drafting (Phil) plus a one-time emulator spot-check on the first
translated batch.

## Ground rules

- The `.nds` ROM is a personal copy — **never commit it** (`.gitignore` covers
  `*.nds`). `extracted/` and `tools/venv/` are gitignored too; regenerate.
- Keep `docs/FORMAT_NOTES.md` as the source of truth; the skills point to it.

## Continuing on another machine

All code, docs, and skills are on GitHub (`origin/main`). Three things are
**not** in git — two regenerate themselves, only the ROM must be moved by hand:

| Thing | In git? | How to get it |
|---|---|---|
| the `.nds` ROM (~513 MB) | no (`*.nds` ignored) | **copy manually** (USB / private cloud / scp) — never through git |
| `extracted/` (~453 MB) | no | **regenerate**: `python3 extract_rom.py` |
| `tools/venv/` (~17 MB) | no | **regenerate**: `python3 -m venv venv && pip install ndspy` |

Setup steps:

```bash
# 1. clone the tracked project
git clone https://github.com/McPe4ce/ie3Ogres-rom-FR.git
cd ie3Ogres-rom-FR

# 2. copy the ROM into the repo root by hand, exact same filename:
#    Inazuma-Eleven-3-Sekai-heno-Chousen-The-Ogre-DS-Traduit-en-Français-v06.nds

# 3. recreate the Python env
cd tools && python3 -m venv venv && source venv/bin/activate && pip install ndspy

# 4. rebuild the extracted filesystem (needs the ROM from step 2)
python3 extract_rom.py

# 5. sanity check — both should pass cleanly
python3 evet_slots.py evet     # 0 round-trip failures, full-pkb identical
python3 ie3_codec.py           # all "OK"
```

Notes:
- **In-progress translation JSON** (e.g. `evet_jp.json`) is not auto-tracked —
  only `.py`/`.md` have been committed. To carry half-finished translations
  between machines, commit the JSON deliberately (`git add tools/evet_jp.json`)
  or copy it alongside the ROM. It's small; committing is easiest.
- The bypass-permission settings live in `~/.claude/settings.local.json` on the
  current machine only — not part of the project; re-add on the new machine if
  wanted.
