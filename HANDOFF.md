# Handoff — current state

Quick orientation for the next session. Full detail is in
[`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md) (source of truth) and the four
skills in `.claude/skills/`. Read [`README.md`](README.md) first.

## Where we are (2026-07-21)

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
| **Translating the text** | 🔶 **in progress** — `item.STR` ✅ **822/822** and `unitbase.STR` ✅ **2374/2374** done (both repack-verified). Next: menu leftovers (65) then `evet.pkb`. |
| Emulator test | ✅ **item.STR validated in melonDS** (2026-07-20) via a debug-room ROM — all item descriptions render, longest lines reflow fine. See `docs/EMULATOR_TEST.md`. Reusable debug ROM + cheats in `Téléchargements\IE3-Ogre-FR-test\`. |

## Translation progress & how to resume (start here tomorrow)

- **Read the `ie3-translation` skill first** — it has the house style, the
  two-encoding rule, terminology, and the per-format workflow.
- **`item.STR`: ✅ 822/822 done** (finished 2026-07-20), saved in
  `translations/item.json` (the durable artifact — the scratchpad `.nds`/`.STR`
  builds are gone, but this JSON isn't). The final 374 gear entries were filled
  using the new team glossary; QA passed: encoder 822/822 clean (0 skips),
  repack `--verify` OK (only `item.STR` differs, 79296→111776 bytes — `.STR`
  has no budget so growth is fine). Stat-token convention set for gear:
  キック→**Tir**, スピード→**Vitesse**, ガード→**Défense**, コントロール→**Contrôle**,
  ガッツ→**Cran**, ボディ→**Corps**, スタミナ→**Endurance**, ＴＰ→**TP**.
  Gotcha found: avoid ASCII `"` double-quotes (str_codec maps them to full-width
  ＂ which SJIS can't encode — use no quotes or single `'`).
  Rebuild the patched file anytime:
  ```bash
  python3 str_reinsert.py ../translations/item.json --out item_new.STR
  python3 repack_rom.py -r data_iz/logic/item.STR=item_new.STR -o patched.nds --verify
  ```
  Done so far: consumables, travel/route tickets, spirit emblems, story/key
  items, command/skill effect strings, and **all 352 技の秘伝書 technique
  manuals** (done by formula — see the skill).
- **Next up (suggested order):** the **menu leftovers** `command.STR` (8),
  `games.STR` (43), `rpgtitle.STR` (14) — ~65 entries total, and finishing them
  closes out **every `.STR` file in the ROM**. Then `evet.pkb` (~15,756 chunks,
  the big one — and **budget-checked**, unlike `.STR`, so expect to tighten
  wording; `evet_reinsert.py` refuses to write and lists overflowing slots).
- ~~**Remaining item.STR (374):**~~ ✅ done. Was: flavour gear — uniforms, spikes, gloves,
  misangas/pendants, formations, GK-shoe names — all reference **team &
  character names**. **Team-name glossary: ✅ built (2026-07-20)** — see the new
  "Teams, clubs & national selections" section in `docs/NAME_GLOSSARY.md`, mined
  by grepping the shipped FR `evet` dialogue (11,264 FR chunks). Confirmed from
  the ROM's own FR: Raimon, Kirkwood (世宇子), Royal Académie (帝国), Ogre,
  Cotarl, Zeus, Académie Alius + Gemini Storm/Epsilon/Diamond Dust/Prominence/
  Chaos, and the FFI squads (Les Empereurs=Argentine, The Kingdom=Brésil,
  Orphée=Italie, Licornes=USA, Big Waves=Australie, Dragons de feu=Corée, Lions
  du désert=Qatar). Still `🔤`/`⚠️` (not in ROM FR, verify): 白恋 Hakuren,
  傘美野 Kasamino, 漫遊寺 Manyuji, 大海原 Omihara, 陽花戸/Occult, Galz, Genesis.
  **Next step:** finish the 374 gear entries in `translations/item.json` using
  that glossary. Same glossary now unblocks `unitbase.STR` (2374 bios) + `evet`.
- **`unitbase.STR`: ✅ 2374/2374 done** (finished 2026-07-21), saved in
  `translations/unitbase.json`. QA passed: encoder **2374 edits / 0 skipped**,
  0 lines over 65 chars, 0 ASCII double-quotes, and a whole-ROM
  `repack_rom.py --verify` OK (1985 files + arm9/arm7 + 133 overlays intact;
  271840→391328 bytes — `.STR` has no budget so growth is fine).
  - **Method that paid off — mine the ROM, don't trust memory.** Every recurring
    name was grepped against the 11,264 shipped-FR `evet` chunks before use.
    That produced real corrections: FR uses **Gazelle** (not "Gazel"),
    **Rococo Urupa** is FR-attested, and 久遠 is a **coach** (久遠監督 ×38), not a
    place. 17 new glossary rows, each with its evidence + confidence mark.
  - **Duplicates were auto-filled, never retyped.** ~60 entries repeat an
    earlier `src` verbatim (the 8 "mystery man" bios, ~30 Heaven/Hell bios,
    and 2364–2379 which repeat the main cast). They were filled
    programmatically from the already-translated text so the same character
    never reads two different ways. Reusable snippet:
    ```python
    done = {e['src']: e['fr'] for e in d['entries'] if e.get('fr')}
    dup  = {e['idx']: done[e['src']] for e in d['entries']
            if not e.get('fr') and e['src'] in done}
    ```
- **⚠️ OWED: the gender sweep (53 entries).** Japanese bios are often
  grammatically genderless; French forces an agreement. Where the JP marked it
  (女子, 彼女, 娘, くのいち…) the choice is settled. Where it didn't, the entry
  carries **`"gender_check": true`** in `translations/unitbase.json` — a durable,
  machine-readable to-do list that travels with the artifact. These are
  *candidates*, not known errors. To resolve: the bio index maps to a player
  unit, so the in-game portrait settles it — use the debug ROM, then flip the
  handful that are wrong (isolated one-line edits, no re-translation).
  `python3 tools/flag_gender.py --list` prints them; the flags can be stripped
  once resolved.
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
2. ~~**Emulator visual spot-check**~~ ✅ **done on `item.STR` (2026-07-20)** —
   see `docs/EMULATOR_TEST.md`. All item descriptions render in melonDS and the
   longest lines (65 full-width chars) reflow correctly; uniforms cleared by
   width analysis. **Reusable test setup** (regenerate anytime, see the guide):
   build a debug-room ROM by flipping `RPG_SCRIPT_NO 31010000→39010000` in
   `data_iz/INAZUMA.INI` and repacking it alongside the edited file — it boots
   straight past the intro into a debug room with team/menu access. BOEJ
   Action Replay cheats (all equipment/uniforms/items) live in
   `ie3_cheats_melonds.txt` (paste into melonDS; `94000130…` blocks = hold
   SELECT). For each future batch (`unitbase`, `evet`) do the same: repack a
   debug ROM with the edit + `--verify`, then eyeball the longest new lines.
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
