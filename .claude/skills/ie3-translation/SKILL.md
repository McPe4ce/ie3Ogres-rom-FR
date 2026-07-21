---
name: ie3-translation
description: Use when actually translating this Inazuma Eleven 3 (Ogre) ROM's untranslated Japanese into French — drafting/writing the French text that fills the gaps, choosing wording, applying character-name conventions, or reasoning about translation house style. Triggers on "translate the items", "translate this dialogue", "fill in the French for unitbase", "what's the French name for this player", "continue the translation", or any task that produces French text to reinsert. For the byte formats/tools themselves see ie3-pkb-pkh-format, ie3-str-format, ie3-french-encoding, ie3-rom-extraction.
---

# IE3 (Ogre) French translation — house style & workflow

Goal: fill the untranslated Japanese gaps in the partially-translated v06 French
patch, **matching the existing translation's style** so new text is seamless.
Translate for **meaning**, not word-by-word — natural French a French player
would read, within DS text-box limits. The mechanics/tools are covered by the
format skills; this skill is about *the French itself*.

## Golden rules

1. **Meaning over literal.** Convey what the line does/says in idiomatic French.
   Keep tone: kids' sports anime — energetic, informal, exclamatory.
2. **Names: official European (English-dub) names**, kept **constant**. The
   shipped patch already uses them (protagonist マモル/円堂 → **Mark**, plus
   Nathan, Dr.Killard…). See `docs/NAME_GLOSSARY.md`. Unknown/obscure NPC →
   Hepburn **romaji**, and record the choice in the glossary so it stays constant.
3. **Preserve structure.** Keep `\n` line breaks roughly where they are (they set
   DS text-box line wrapping); keep control bytes (handled by the tools, never in
   your text); keep stat tokens like `GP`, `TP`, `SC`, `+9` verbatim.
4. **Drop furigana.** Source kanji carry readings like `[水/みず]`, `[回復/かいふく]`
   — translate the *meaning* (`[水/みず]` → "eau") and drop the reading entirely.
5. **Two different text encodings — pick per file (critical):**

## ⚠️ Two encodings — do not mix them up

| Where | Encoding | Accents? | Tool |
|---|---|---|---|
| **`evet.pkb` dialogue** | single-byte, custom | **lowercase accents OK** (é è à ç ê î ï ô ù û) | `ie3_codec.encode_text` |
| **`*.STR` menus/descriptions** | full-width SJIS Latin | **NO accents** (folded to ASCII) | `str_codec.encode_str_fr` |

You may **write natural accented French either way** — each encoder folds what its
target can't show (`str_codec` strips all accents: "Défense"→"Defense"; `ie3_codec`
keeps lowercase accents, folds uppercase accents / `ë ö ü œ æ` / `« »` to ASCII).
Both report their folds. Sentence-initial capitals therefore come out **unaccented**
in both ("À"→"A", "É"→"E") — that's the established house style, don't fight it.
Straight ASCII apostrophe `'` is correct in your text (str_codec maps it to the
game's `’`; evet keeps ASCII). Reinsertion tools already call the right encoder.

## Categories → files (what to translate, and in what order)

Recognised by file, not by guessing. Untranslated counts as of 2026-07-19:

| Category | File | Untranslated | Names? | Notes |
|---|---|---|---|---|
| Item descriptions | `logic/item.STR` | 822 | almost none | **best first** — formulaic |
| Player bios | `logic/unitbase.STR` | 2374 | **heavy** | needs the name glossary |
| Story dialogue + choices + system msgs | `script/evet.pkb` | ~15,756 chunks | heavy | biggest; do in batches |
| Menu leftovers | `logic/{command,games,rpgtitle}.STR` | 8 / 43 / 14 | light | quick cleanups |
| (already done) | `logic/{tacticscmd,sp_binder}.STR` | 0 | — | skip |

Within `evet.pkb` a single slot bundles narration + choice options + battle
messages together (see the parts of one slot), so you can't cleanly split
"dialogue" vs "choice box" structurally — translate a slot as a coherent unit.

## Established terminology (mined from the shipped French — match it)

- **Stats/keep as-is:** `GP`, `TP` (energy stats — never translate), `SC`, `+N`.
- **Stat names:** Tir (kick/shoot), Défense, Attaque (dribble techniques),
  Vitesse, Gardien (keeper), Endurance, Contrôle. (In `.STR` these render
  unaccented: "Defense", "Controle" — the encoder handles it.)
- **Football verbs (from command.STR):** Feinte, Dribble, Esquive, Contact,
  Tacle, Blocage, Tir, Lob, Volée, Tête, Arrêt, Coup de poing.
- **Elements (attributes):** 火 Feu · 山 Terre · 風 Air · 林 Bois.
- **Recovery verb + scale** (item descriptions, agreed with Phil): verb is
  **"Restaure … de GP/TP"**; the 4 intensity tiers are
  ちょっと **"un peu"** · そこそこ **"pas mal"** · かなり **"beaucoup"** ·
  ぜんぶ **"la totalité"** (e.g. "Restaure la totalité du GP !").
- **秘伝書** (technique manual): translated **by formula** — these read
  `element / TP / N人 / modifiers \n <type>技の秘伝書` and become
  `{Elem} / TP {n} / {N} joueur(s) / {mods}` + newline + the type line:
  シュート技→"Manuel de technique de tir", キーパー技→"…de gardien",
  オフェンス技→"Manuel de technique offensive", ディフェンス技→"…défensive".
  Modifier vocab: ロング→"Longue distance", キャッチ→"Prise",
  パンチング(２)→"Poing (2)", Ｌ/Ｍ/Ｓサイズ→"Taille L/M/S", 女性→"Fille",
  風/火キャラ→"Perso Air/Feu", ＳＣ/ＳＢ kept as-is. Elements: 火 Feu · 山 Terre ·
  風 Air · 林 Bois · なし Aucun. (Watch: a modifier can wrap onto the type line —
  parse the type as a *suffix*, not "line 2". Strip furigana first.)
- **陣形** (formation): "Formation". Keep the formation number verbatim
  (`４−４−２` → `4-4-2`).
- **Equipment stat tokens** (gear descriptions, e.g. `キック＋６`): キック→**Tir**,
  スピード→**Vitesse**, ガード→**Défense**, コントロール→**Contrôle**,
  ガッツ→**Cran**, ボディ→**Corps**, スタミナ→**Endurance**, ＴＰ→**TP**.
  Render as `Tir +6\n<flavour line>`.
- **Team names in gear:** use `docs/NAME_GLOSSARY.md` → "Teams" section. Note the
  country-uniform items (`アルゼンチン用`, uniform 956 etc.) use the **country
  label** ("Argentine"), not the FFI team name — only full uniform *descriptions*
  that evoke the squad use the team name (Les Empereurs, The Kingdom, …).
- Recovery tiers are the item scale above. Command/skill *effect* strings
  ("成功率アップ" etc.) → "Augmente la réussite de…".
- **`.STR` gotcha:** never use ASCII `"` double-quotes — `str_codec` maps them
  to full-width `＂` which SJIS can't encode (reinsert skips the record). Use no
  quotes, or single `'` (which round-trips to the game's `’`).
- **Line length:** keep every line **≤ 65 chars** — that's the longest line
  empirically proven to render in the 2-line box (confirmed in melonDS, see
  `docs/EMULATOR_TEST.md`). Benign codec substitutions: `'`→`’` and `-`→`−`
  (full-width minus). Both are attested in the shipped FR; don't "fix" them.

## ⚠️ Gender agreement (JP is genderless, French isn't)

Japanese bios/dialogue frequently give **no gender signal at all**, but French
forces an agreement on every adjective and participle. Rules:

1. **Use the JP marker when there is one** — 女子, 彼女, 娘, 少女, くのいち,
   紅一点, 妹, ～ちゃん, and role nouns (巫女, 看板娘) all settle it.
2. **When there is no marker, default masculine** (matches the unmarked JP and
   the rest of the corpus) **and flag the entry** rather than guessing silently.
3. **Flag durably, in the artifact** — add `"gender_check": true` to the entry
   in the translation JSON. It survives session loss, travels with the file, and
   is machine-readable. Resolve later against the in-game portrait; a wrong
   guess is a one-line edit, never a re-translation.

Currently 53 flagged in `translations/unitbase.json`. Expect the same issue in
`evet.pkb` for any speaker whose gender isn't established by context.

## Duplicates: reuse, never retype

Long `.STR` files repeat the same `src` verbatim (in `unitbase` ~60 entries: the
8 "mystery man" bios, ~30 Heaven/Hell bios, and 2364–2379 repeating the main
cast). **Identical Japanese must get byte-identical French**, or the same
character reads two different ways in-game. Fill them programmatically:

```python
done = {e['src']: e['fr'] for e in d['entries'] if e.get('fr')}
dup  = {e['idx']: done[e['src']] for e in d['entries']
        if not e.get('fr') and e['src'] in done}
```

## Names: mine the ROM, don't trust memory

Before using any recurring name, grep the **shipped FR `evet` chunks** for it
(`evet_dump.py evet -o evet_all.json`, then filter `cls == 'fr'`). This is not
optional politeness — it catches real errors: the FR patch uses **Gazelle**
(not the English "Gazel"), **Rococo Urupa** is attested verbatim, and 久遠 turns
out to be a **coach** (久遠監督 ×38), not a place name. Record every decision in
`docs/NAME_GLOSSARY.md` with its source and a confidence mark (✅ ROM-attested /
⚠️ reasoned / 🔤 romaji fallback). Also watch for collisions: **IQ** is a
character (アイキュー) but **QI** is the French stat — never unify them.

## Workflow (per format)

**`.STR`:**
```bash
python3 str_dump.py item --jp-only -o item_jp.json   # dump untranslated JP
#  ... fill each entry's "fr" field (leave "" to skip) ...
python3 str_reinsert.py item_jp.json --out item_new.STR   # full-width encode, byte-safe
python3 str_slots.py item                              # (optional) round-trip sanity
python3 repack_rom.py -r data_iz/logic/item.STR=item_new.STR -o patched.nds --verify
```
**`evet.pkb`:**
```bash
python3 evet_dump.py evet --jp-only -o evet_jp.json
#  ... fill "fr" fields ...
python3 evet_reinsert.py evet_jp.json --out evet_new.pkb   # BUDGET-CHECKED (see below)
python3 repack_rom.py -r data_iz/script/evet.pkb=evet_new.pkb -o patched.nds --verify
```

## Budgets & length

- **`.STR` has NO budget** — strings resize freely (ordinal index). Write what
  reads best; just keep it sane for a DS text box.
- **`evet.pkb` IS budget-checked** — each slot owns a fixed byte span.
  `evet_reinsert.py` refuses to write and lists overflowing slots; shorten those.
  French is often longer than Japanese, so expect to tighten wording.
- Keep lines short enough not to overflow the box horizontally; respect existing
  `\n`. When unsure, mirror the length/'\n' rhythm of nearby already-French lines.

## QA checklist before repacking

- No-op reinsert (empty edits) reproduces the original byte-for-byte — the tools
  guarantee this; if it ever fails, stop.
- Re-decode a few edited records (`str_codec.decode_str_fr` / `ie3_codec.decode_text`)
  and eyeball them.
- Check the folds report for anything unexpected (an accent you didn't intend to
  lose, a `«»`/`œ` you should rephrase).
- For `evet`, confirm 0 overflow slots (or shorten and re-run).
- Repack with `--verify`; confirm only the intended file(s) differ from the ROM.
- Visual emulator spot-check is owed on the **first real batch** (reflow of
  newly-sized strings) — encoding itself is already proven by the shipped patch.

## Keeping this skill current

Append every new name decision to `docs/NAME_GLOSSARY.md` immediately (constancy
is the whole point). If you discover a new house-style term or a format wrinkle,
note it here and in `docs/FORMAT_NOTES.md`.
