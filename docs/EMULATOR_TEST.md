# Emulator test — item.STR French, via debug room (melonDS)

Goal: visually confirm the **374 newly-translated gear descriptions** render and
reflow correctly on a DS screen. This is the "first real batch" spot-check owed
in the project plan. The debug ROM below **boots straight into the debug room**,
skipping the whole intro.

## Files
On this machine both live in **`Téléchargements\IE3-Ogre-FR-test\`**
(`C:\Users\philg\Downloads\IE3-Ogre-FR-test\`):
- **`IE3-Ogre-FR-DEBUG.nds`** — your v06 French ROM **+ the full item.STR
  translation + debug boot**. Use this for testing only. *(Gitignored like all
  `*.nds`; regenerate anytime — see "How it was built" below.)*
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
# 2. rebuild translated STR
python3 str_reinsert.py ../translations/item.json --out /tmp/item_new.STR
# 3. repack both edits into one ROM
python3 repack_rom.py \
  -r data_iz/logic/item.STR=/tmp/item_new.STR \
  -r data_iz/INAZUMA.INI=/tmp/INAZUMA_debug.INI \
  -o ../IE3-Ogre-FR-DEBUG.nds --verify
```
`RPG_SCRIPT_NO` lives in `extracted/data_iz/INAZUMA.INI` (line 42). Revert to
`31010000` for a normal-booting build. Source: debug mode documented on GBAtemp
(EU/JP share the `31010000` default); cheats from inazumalife.com (BOEJ).
