# Emulator test — item.STR French, via debug room (melonDS)

Goal: visually confirm the **374 newly-translated gear descriptions** render and
reflow correctly on a DS screen. This is the "first real batch" spot-check owed
in the project plan. The debug ROM below **boots straight into the debug room**,
skipping the whole intro.

## Files
On this machine both live in **`Téléchargements\IE3-Ogre-FR-test\`**
(`C:\Users\philg\Downloads\IE3-Ogre-FR-test\`):
- **`IE3-Ogre-FR-DEBUG.nds`** — your v06 French ROM **+ the full item.STR and
  unitbase.STR translations + debug boot** (rebuilt 2026-07-21). Use this for
  testing only. *(Gitignored like all `*.nds`; regenerate anytime — see "How it
  was built" below.)*
- **`ie3_cheats_melonds.txt`** — Action Replay codes (all equipment / uniforms /
  items / money) for game code **BOEJ**. *(Master copy also kept at repo root.)*

> Keep your normal playthrough ROM separate — the debug ROM replaces the boot
> script, so it always lands in the debug room, not the story.

## 1. Load it in melonDS
1. Launch **melonDS** → *File ▸ Open ROM…* → pick `IE3-Ogre-FR-DEBUG.nds`.
2. It boots into the **debug room** instead of the intro. Interact with the
   icons walking around:
   - **star** = organise/def your team (gives you players to equip)
   - **cat** = grants a ready-made player
   - **fox/dog** = recruiting menu
   - **rabbit** = instant match vs Wild Jr.
   - **red robot** = capsule machine · **chicken** = practice battle
3. Get a team (star/cat), then open the **equipment menu (装備 / Équipement)** and
   start browsing gear — the **description text is what you're checking**.

## 2. Add the cheats (so every one of the 374 is viewable)
Most gear is late-game, so cheat the inventory full first.

In melonDS: load the ROM, then open the **cheat manager** (recent builds:
titlebar menu ▸ *"Setup cheats"* / *"Cheat codes"*). **Add new cheat**, paste a
block from `ie3_cheats_melonds.txt`, tick it **enabled**, then **reset** the game
(*System ▸ Reset*). Codes with a `94000130…` first line are **button-activated**
(hold **SELECT** in-game to apply); the "All Equipment x99" block is
always-on.

Recommended: enable **All Equipment x99** + **All Uniforms (always-on)** — those
two cover the riskiest long strings (gloves +17/+18, FFI kits, uniforms). The
`94000130…` blocks are **hold-SELECT** activators (not L+R); the always-on
uniform variant needs no button. Uniforms are changed from the **team menu**, not
the per-player equipment screen.

## 3. Speed & convenience hotkeys (melonDS)
- **Fast-forward / no frame limit:** hold the fast-forward key (default **Tab**;
  check *Config ▸ Input/Hotkeys*). Use it to blitz any loading/menus.
- **Save state:** *File ▸ Save state ▸ slot* (or the hotkey). Do this **once**
  after you've got a team + equipment menu open — then reload the state to jump
  back instantly instead of redoing the debug-room setup.

## 4. What to actually look at
You are checking **layout, not spelling** (encoding is already byte-proven):
- Does any description **overflow the text box** horizontally or get cut off?
- Do the **two-line** uniform/wear descriptions wrap where intended (the `\n`)?
- The **longest** strings — check these first:
  - FFI gloves at +16/+17 (items 997–1007), the Empereurs/Kingdom/Orphée
    uniforms (956–960), the multi-clause formations (474–483), and the
    "Restaure…" consumables.
- Accents render **unaccented** on menus by design (house style — "Défense" →
  "Defense"). That's expected, not a bug.

If something overflows, note the item; the fix is just shortening that entry's
`fr` in `translations/item.json` and rebuilding — no tooling change.

## How it was built (to regenerate)
```bash
cd tools && source venv/bin/activate
# 1. debug INI: RPG_SCRIPT_NO 31010000 -> 39010000 (boot script -> debug room)
sed 's/RPG_SCRIPT_NO=31010000/RPG_SCRIPT_NO=39010000/' \
    ../extracted/data_iz/INAZUMA.INI > /tmp/INAZUMA_debug.INI   # same 5725 bytes
# 2. rebuild the translated STR pools
python3 str_reinsert.py ../translations/item.json     --out /tmp/item_new.STR
python3 str_reinsert.py ../translations/unitbase.json --out /tmp/unitbase_new.STR
# 3. repack all edits into one ROM
python3 repack_rom.py \
  -r data_iz/logic/item.STR=/tmp/item_new.STR \
  -r data_iz/logic/unitbase.STR=/tmp/unitbase_new.STR \
  -r data_iz/INAZUMA.INI=/tmp/INAZUMA_debug.INI \
  -o ../IE3-Ogre-FR-DEBUG.nds --verify
```
Expected on the 2026-07-21 build: `item.STR` 79296→111776, `unitbase.STR`
271840→391328, `INAZUMA.INI` unchanged size, then
`verify OK: all 1985 files, arm9/arm7, and 133 overlays round-trip intact`.
`RPG_SCRIPT_NO` lives in `extracted/data_iz/INAZUMA.INI` (line 42). Revert to
`31010000` for a normal-booting build. Source: debug mode documented on GBAtemp
(EU/JP share the `31010000` default); cheats from inazumalife.com (BOEJ).

## Results (2026-07-20) — item.STR PASSED ✅
- Debug ROM boots straight into the debug room (intro skipped) — **works**.
- **All Equipment x99** always-on code populated the inventory; **all item
  descriptions render** correctly in the equipment menu, including the longest
  strings (item lines up to **65 full-width chars** reflow fine in the 2-line
  box). Accents show unaccented on menus, as designed.
- **Uniforms:** the in-game team-uniform browse menu wasn't located during this
  session (the always-on uniform code was added but the list screen wasn't
  found). This is **not** an open risk: the uniform descriptions use the same
  file/encoder/2-line box, and a width check shows the **longest uniform line is
  53 chars vs the 65-char item line already proven to render** — every uniform
  line sits inside the validated envelope (0 lines over). Uniforms are cleared
  by construction; a visual pass can be done opportunistically later if desired.
- **Conclusion:** `item.STR` (822/822) is validated on real hardware. The owed
  "first real batch" emulator spot-check is **done**. Future batches
  (`unitbase.STR`, `evet`) can reuse this debug ROM + cheat setup.

## unitbase.STR added (2026-07-21) — two things to check in-game

The debug ROM now also carries **`unitbase.STR` (2374/2374 player bios)**.
Build QA passed (encoder 2374/0 skipped, 0 lines >65 chars, repack `--verify`
OK), so **encoding and reflow are not at risk** — bios use the same 2-line box
and the same 65-char envelope already proven by `item.STR`. Two open questions
need *eyes*, not tooling:

1. **⚠️ The gender sweep (53 entries) — the one real to-do.** Japanese bios are
   often genderless; French forces an agreement, and where the JP gave no
   signal the entry was defaulted and flagged `"gender_check": true` in
   `translations/unitbase.json`. **How to check:** view a flagged player's bio
   in-game (bio index ↔ player unit) and see whether the portrait is male or
   female. Wrong ones are isolated one-line edits in the JSON — no
   re-translation, just flip the agreement and rebuild. List them with
   `python3 tools/flag_gender.py --list`.
2. **Hyphenated line breaks (3 entries).** Bios 1521, 2161 and 2162 needed a
   word split across the line break (`l'agri-\nculture`, `l'élec-\ntricité`,
   `poissons-\nchats`) to fit 65 chars. Confirm these render acceptably; if
   not, reword — each is a single self-contained entry.

Where to look: the bios show on the **player/roster info screen**, so the
"All Equipment" cheat isn't needed — use the debug room's star/cat icons to get
players, then open a player's info.
