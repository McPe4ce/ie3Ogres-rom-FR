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
| **Translating the text** | 🔶 **in progress** — **all `.STR` files done**; `evet.pkb` **1064/15,742** (story-critical-subset strategy, see below): `item.STR` ✅ 822/822, `unitbase.STR` ✅ 2374/2374, `command.STR` ✅ 8/8 (all repack-verified); `games`/`rpgtitle` carry no real content (residue only). Next: `evet.pkb`. |
| Emulator test | ✅ **item.STR validated in melonDS** (2026-07-20) via a debug-room ROM — all item descriptions render, longest lines reflow fine. See `docs/EMULATOR_TEST.md`. Reusable debug ROM + cheats in `Téléchargements\IE3-Ogre-FR-test\`. |

## ▶ NEXT SESSION — exact steps (evet.pkb, resume at rec 148)

**State as of 2026-07-22:** every `.STR` file is done. `evet.pkb` is **1064/15,742
JP chunks** translated (recs 92–100, 103–136, 145–147 added 2026-07-22; reinsert-verified: 1064 edits,
0 skipped, `.pkb` still exactly 2,926,480 bytes; round-trip decode clean). The
master artifact is `translations/evet.json` — it holds **all 39,610 entries**
(already-French ones included, for context) and accumulates across sessions.

**SCOPE DECISION MADE (2026-07-22): story-critical subset first.** Walk rec order
(≈ story order), translate substantive story-cutscene recs, and **skip/defer**:
recruitment scenes (386 recs / 3,248 chunks, tell: `%s rejoint l'équipe!` /
`Bonne recherche!` scaffolding), the NPC/tutorial/shop flavor band recs
1500–2100 (365 recs / 678 chunks), and short one-liner recs (<8 todo chunks).
Story spine ≈ **480 recs / ~10,500 chunks**. Signal work: a rec is side content
if its FR chunks carry recruitment scaffolding, or it's a 1–2-chunk NPC line.
Verify per rec by reading it (needed anyway).

**Resume at rec 148.** Done through rec 147 (recs 136, 145–147 this pass). Recs
137–144 are tiny side beats (DEFERRED with 101–102, 114–123, 133). Next block:
148 (41) → 149 (34) → 150 (23)... **⚠️ name note:** 瞳子=**Hitomiko** (NOT "Toko"
— collides with 塔子=Touko); 砂木沼=**Saginuma**, codename デザーム=**Desarm**.
(塔子/音無 resolved: 音無=Celia, 塔子=Touko.)

### The loop, exactly

```bash
cd /home/mcpeace/ie3Ogres-rom-FR/tools && source venv/bin/activate

# 1. See what's next (prints the next slots + their untranslated chunk counts)
python3 - <<'EOF'
import json
d=json.load(open('../translations/evet.json'))
jp={}
for e in d['entries']:
    if e['cls']=='jp' and not e.get('fr') and e['src'].strip():
        jp[e['rec']]=jp.get(e['rec'],0)+1
n=[r for r in sorted(jp)][:12]
print('resume at rec',n[0]); print([(r,jp[r]) for r in n],'=',sum(jp[r] for r in n),'chunks')
EOF
```

**2. Read the slot WITH its French neighbours before translating.** Slots are
interleaved — JP chunks sit between already-French ones, and you must match the
surrounding register (formal/informal, `tu`/`vous`). Print a slot with:

```bash
python3 - <<'EOF'
import json
REC=92                                    # <- the slot you're working on
d=json.load(open('../translations/evet.json'))
for e in sorted((x for x in d['entries'] if x['rec']==REC), key=lambda x:x['part']):
    todo = e['cls']=='jp' and not e.get('fr')
    print(f'{"JP>" if todo else "   "} p{e["part"]:<3} [{e["cls"]}] {e["src"]!r}')
EOF
```

**3. Mine every recurring name from the ROM before using it** (non-negotiable —
it has caught real errors every single batch):

```bash
python3 - <<'EOF'
import json,re
d=json.load(open('../translations/evet.json'))
FR=[e['src'] for e in d['entries'] if e['cls'] in ('fr','ascii')]
for c in ['Jude','Axel','Nathan']:                 # <- names in your slot
    h=[s for s in FR if re.search(r'\b'+c,s)]
    print(f'{c:<10} x{len(h):<3}', repr(h[0])[:70] if h else '— (no attestation -> romaji, log it)')
EOF
```

Confirmed so far: 円堂→**Mark**, 鬼道→**Jude**, 豪炎寺→**Axel**, 風丸→**Nathan**,
吹雪→**Shawn**, 佐久間→**Caleb**, 立向居→**Darren**, 木暮→**Scotty**, 塔子→**Touko** *(NOT Celia — see glossary; 音無=Celia)*,
木野→**Silvia**, 一之瀬→**Erik Eagles** *(plural — the ROM writes it that way)*,
土門→**Bobby**, 壁山→**Jack**, 綱海→**Hurley**, ヒロト→**Xavier**, 緑川→**Jordan**,
染岡→**Kevin**, 音無（春奈）→**Celia**, 雷門夏未→**Nelly**, 木野→**Silvia**,
冬花→**Camelia** *(not a transliteration)*,
響木→**Coach Hillman**, イナズマジャパン→**Inazuma Japon** (plain — 657× in FR;
brackets only in the rare set-piece "L'[Inazuma Japon!]"). ミスター・エンドウ→
**Monsieur Evans** (surname Evans, FR ×57). ヒビキ提督→**l'amiral Hillman** (FR-attested).
Romaji fallbacks (no ROM attestation): Toby, Toramaru, Fudou, Hijikata, Rika, Touko,
Suzume, Megane, Nice Dolphin, Manyuji, Hakuren, Kuon. Techniques get **translated**,
not transliterated: ゴッドハンド→"Main céleste" (shipped), so ザ・ウォール→**"Le Mur"**.

**4. Write the French into the master artifact** (keyed by `(rec, part)`):

```bash
python3 - <<'PYEOF'
import json
FR={ (92,0):"...", (92,4):"...", }          # <- your batch
d=json.load(open('../translations/evet.json'))
n=0
for e in d['entries']:
    if (e['rec'],e['part']) in FR and e['cls']=='jp':
        e['fr']=FR[(e['rec'],e['part'])]; n+=1
json.dump(d,open('../translations/evet.json','w'),ensure_ascii=False,indent=1)
print(f'applied {n}/{len(FR)}')
PYEOF
```

**5. Gate, reinsert, repack, deploy** — always in this order:

```bash
python3 evet_fit.py ../translations/evet.json          # MUST pass before step 2
python3 evet_reinsert.py ../translations/evet.json --out /tmp/evet_new.pkb
python3 repack_rom.py \
  -r data_iz/logic/item.STR=/tmp/item_new.STR \
  -r data_iz/logic/unitbase.STR=/tmp/unitbase_new.STR \
  -r data_iz/logic/command.STR=/tmp/command_new.STR \
  -r data_iz/script/evet.pkb=/tmp/evet_new.pkb \
  -o /tmp/IE3-Ogre-FR-NORMAL.nds --verify
cp /tmp/IE3-Ogre-FR-NORMAL.nds /mnt/c/Users/philg/Downloads/IE3-Ogre-FR-test/
```
(`/tmp/*_new.STR` won't survive a reboot — regenerate with
`python3 str_reinsert.py ../translations/<file>.json --out /tmp/<file>_new.STR`.)

**Two invariants that prove the batch is sound:** `evet_reinsert.py` must report
**0 skipped**, and the new `.pkb` must be **exactly 2,926,480 bytes** — identical
to the original. A different size means a slot span moved and every later offset
is wrong; stop and investigate rather than shipping it.

### Hard-won gotchas — do not rediscover these

- **The budget rule is PER-PART, not per-slot.** Growth is absorbed by zero-runs
  *at or after* the edited chunk, each keeping 1 terminator zero; it cannot
  borrow padding from earlier parts. A "slot total ≤ budget" model looks right
  and silently passes edits the tool rejects. **Never re-derive the rule** —
  `evet_fit.py` calls the real `set_chunk_bytes()` so it matches by construction.
  ~3% of chunks need shortening; expect 1–2 per batch, they're usually over by a
  few bytes and a shorter synonym fixes it.
- **Accents ARE correct in evet dialogue** — hardware-confirmed 2026-07-21
  (`frère`, `écran`, `Entraînement`). Only `.STR` menus strip them. Write natural
  accented French; the encoder folds uppercase accents (`Ç`→`C`, `É`→`E`) as
  house style. Avoid `«»`/`œ` (they fold too).
- **Blank chunks:** some `jp` chunks are a lone ideographic space `'　'`. Leave
  `fr` empty — do not invent text for them.
- **Duplicates:** identical JP must get byte-identical French.
- **Gender:** JP is genderless. Use the JP marker; if there is none, default
  masculine and set `"gender_check": true` on that entry. Never guess silently.
- **`RPG_SCRIPT_NO` cannot jump to arbitrary scenes.** Tried and failed — bank 31
  holds 13 system/boot scripts and `39010000` (debug room) isn't even an `eve`
  record, so the value is not a record-ID lookup. Scene scripts assume a loaded
  map/party and cold-boot to a black screen. **Verification means playing the
  story**, which is a reason to translate in rec order (≈ story order).
- **`grep` silently fails on `INAZUMA.INI`** (Shift-JIS + mixed CRLF/NEL → treated
  as binary). Use `grep -a`, and verify INI edits with `cmp -l` (expect 1–2
  differing bytes), never file size — a bad `sed` yields an identical-size file.

### Still owed (unchanged)

- **The unitbase gender sweep, 53 entries** — needs in-game portraits, list with
  `python3 tools/flag_gender.py --list`. Use `IE3-Ogre-FR-DEBUG.nds`.
- **The scope decision.** At ~49 chunks/batch this is ~320 more batches. Ask Phil
  whether to keep going exhaustively or cut a **story-critical subset** (main-path
  dialogue only) for a playable French story much sooner. This question has been
  deferred twice; raise it before starting a long run.

## Translation progress & how to resume

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
- ~~**Menu leftovers (65):**~~ ✅ **resolved 2026-07-21 — and the count was wrong.**
  `command.STR` **8/8 done** (the 風林火山 element-change messages; repack-verified,
  1 expected `ê` fold). The other 57 turned out to be **not translatable at all**:
  `rpgtitle.STR` (14) and `games.STR` (43) contain only **patch residue**
  (orphaned tails like `'マジロ'` sitting next to the finished `Super Tatou`), a
  **2010 developer leftover** (`ください 2010/4/8 j_kuramoto`), and **already-French**
  strings that `--jp-only` misread because `°` encodes as katakana bytes.
  **Do not translate them** — those slots are near-certainly dead, but that isn't
  proven from game code, and writing to them would corrupt text that currently
  renders fine. Method + full table in the skill file under "`--jp-only`
  overcounts". **With this, every genuinely-untranslated `.STR` in the ROM is done.**
- **Next up:** `evet.pkb` (~15,756 chunks, the big one — and **budget-checked**,
  unlike `.STR`, so expect to tighten wording; `evet_reinsert.py` refuses to write
  and lists overflowing slots). Worth its own planning pass rather than a cold start.
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
