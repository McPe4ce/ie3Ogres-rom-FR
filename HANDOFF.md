# Handoff — current state

Quick orientation for the next session. Full detail is in
[`docs/FORMAT_NOTES.md`](docs/FORMAT_NOTES.md) (source of truth) and the four
skills in `.claude/skills/`. Read [`README.md`](README.md) first.

## Where we are (2026-07-24)

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
| **Translating the text** | 🔶 **in progress** — **all `.STR` files done**; `evet.pkb` **12,586/15,742 (80%)** — story spine, ≥8-chunk banter/late queue, sub-8 scattered pass, the 101–333 deferred sub-band, AND recs **1500–1836 of the 1500–2100 band** are done: `item.STR` ✅ 822/822, `unitbase.STR` ✅ 2374/2374, `command.STR` ✅ 8/8 (all repack-verified). Remaining evet: **1500–2100 band (255 chunks, resume rec 1838)**, recruitment (2,859), ruby/residue (see below). |
| Emulator test | ✅ **item.STR validated in melonDS** (2026-07-20) via a debug-room ROM — all item descriptions render, longest lines reflow fine. See `docs/EMULATOR_TEST.md`. Reusable debug ROM + cheats in `Téléchargements\IE3-Ogre-FR-test\`. |

## ▶ NEXT SESSION — exact steps (evet.pkb, deferred bands next)

**State as of 2026-07-24 (7th session):** every `.STR` file is done.
`evet.pkb` is **12,183/15,742 JP chunks (77%)** translated (this session:
+472 chunks — the ENTIRE sub-8 scattered pass, PLUS the whole **101–333
deferred sub-band** (FFI-draw / training-ban / delivery-quest / well-wisher /
Knights-of-Queen-party / Argentina-match / USA-Unicorn NPC scenes);
reinsert-verified: 12,183 edits, 0 skipped, `.pkb` still exactly 2,926,480
bytes). The master artifact is `translations/evet.json` — it holds **all
39,610 entries** (already-French ones included, for context) and accumulates
across sessions.

**Next phase, in order:** (1) the **1500–2100 deferred band** (**255 chunks
/ 135 recs left, RESUME AT REC 1838** — recs 1500–1836 done; NPC/tutorial/shop
flavor; watch for more furigana-ruby recs like 975); (2) the **recruitment recs** (**2,859
chunks / 372 recs** — heavily templated: `%s rejoint l'équipe!` scaffolding
is already FR, so expect big dup-fill wins; draft one template rec fully,
then map). To work the band, drop `range(1500,2101)` from the queue-script
`DEFERRED` set (keep `{962,964,972,975,979}|{407}` and the recruitment
filter) and walk in rec order, reading each rec's FR context first.
**⚠️ Deferred fragments (leave untranslated, same policy as ruby recs):**
- rec **199 p91 `たいふう` / p92 `め`** — 2-char hiragana in a done ceremony scene.
- rec **1680** — NEW furigana-ruby rec: p5 is the Ogre-premium technique hint
  (Grand Fire / Gran Fenrir / Tiger Storm) and **p6–p12 = `わざ/わざ/ふか/かんけい/
  なかま/そだ/ひつよう`** are the ruby readings of p5's kanji. Deferred p5, p6–p12
  AND p13 (the whole hint) to avoid orphaning; only p17 (independent flavor)
  was translated. **Add 1680 to the ruby set** `{962,964,972,975,979}`.
- rec **1705 p20 `い`** — lone stray hiragana in the forgetful-old-man rec;
  the rest of 1705 is translated. Skip it.
Furigana-ruby recs 962/964/972/975/979 stay deferred until emulator-tested
(also skip rec 407 p41 'おこな' — patch residue, never translate). NEW format
fact (2026-07-23, in FORMAT_NOTES): original .pkb line breaks are literal
`5C 6E` ("\n" as two ASCII bytes), never 0x0A — but 0x0A IS hardware-proven
to render (slot-18 test had 3-line 0x0A chunks), so real newlines in `fr`
are fine. Page breaks must be written as the literal two-char `\f` sequence
in `fr` (encodes 5C 66); real U+000C is unencodable/unproven.

**Banter-pool method that pays off (keep using it):** before drafting a rec,
build a global `src→fr` map over ALL translated entries and auto-fill any
todo chunk whose JP already exists verbatim (byte-identical FR guaranteed —
late pools are 40–100% duplicates of earlier ones); then draft only the
remaining distinct strings per rec. The snippet + the full **locked tic
table and banter formulas** (~35 speaker voices: Oukikikikii, Sssha!, tchou,
meuh, ma foi, Scandaleux!, Guihihi!, Houngaa!, Kyan, ALL-CAPS robots, foot
de survie, limites humaines, …) now live in the **`ie3-translation` skill**
("Banter tic table") — read it before drafting; do NOT re-invent a tic a
prior rec already fixed. After EVERY batch: `evet_fit.py` (all fit) →
`evet_reinsert.py` (0 skipped) → size check (exactly 2,926,480 bytes).

**⚠️ Queue-script filters (use these):** exclude any rec whose FR chunks match
`rejoint l'équipe|Bonne recherche|vous rejoint` (recruitment — defer per
scope), the deferred bands `101–151 / 165–333 / 288–333 / 1500–2100`, the
furigana-ruby recs `{962, 964, 972, 975, 979}`, and rec `407` (residue-only).
Both the `jp[r]>=8` threshold and the whole sub-8 pass are **done** — that
queue is now empty. The **next** work is the deferred bands (drop them from
`DEFERRED`). The 2141+ recs were extra-route **match-banter pools**: heavy
internal duplicates (fill identical JP with byte-identical FR), one distinct
speaker-voice per rec — the tic for every voice met so far is LOCKED in the
`ie3-translation` skill's "Banter tic table"; look a tic up there before
drafting. NB the 2195–2938 sub-8 penalty-shootout pools (done 2026-07-24) added
shared callouts worth reusing: かんたんに点はやらない！=**Pas de but facile pour
vous!**, フン話にならんな=**Hmpf, c'est pathétique.**, and glitchy katakana-robot
speakers (…カンリョウ, データ通りだな, トウゼンだ) render in **ALL-CAPS French**.

**Remaining-work map (exact, end of 2026-07-24, 7th session):** **3,559 JP
chunks left** in total; the ≥8-chunk queue, the sub-8 scattered pile, AND the
**101–333 deferred sub-band are all EMPTY**. Remaining piles:
1. **1500–2100 deferred band — 255 chunks / 135 recs, RESUME AT REC 1838**
   (recs 1500–1836 done; NPC/tutorial/shop flavor — walk in rec order, dup-fill first);
2. **recruitment recs — 2,859 chunks / 372 recs** (LAST — heavily templated,
   big dup-fill wins expected: draft one template rec fully, then map);
3. **ruby + residue — ~40 chunks** (recs 962/964/972/975/979/**1680** + rec 407 p41 +
   rec 199 p91/p92 + rec 1705 p20): stay deferred/never (see furigana note).
New tics/formulas from 2583–2900 and the sub-8 pass are appended to the
`ie3-translation` skill's banter tic table (Hihihi chuckler, Gwahaha, filles
d'Osaka, American English interjections, heat-lovers, haughty lady
"Écoutez-moi bien:", alien "Sur Terre, on a un dicton:", etc.) — look them up
before drafting anything in that range.

**⚠️ Furigana-ruby chunks (recs 962, 964, 972, 975, 979 — unresolved, all
deferred):** four more ruby recs found 2026-07-23 (962/964/972/979:
shop/hospital/pharmacy/family intros whose main chunk carries `\f` pages +
short hiragana reading tails, e.g. 962 p7 'まえ' p8 'りよう'). Same rule for
all: defer until emulator-tested. Original note: some NPC/tutorial recs carry
one big `\f`-paginated dialogue chunk + a tail of short pure-hiragana chunks
that are **ruby readings** of the kanji words in the main chunk (975: p1–p9 =
じっしゅうしつ/てんすう/…, in order). The main chunk's raw bytes hold **no
inline ruby markers**, so the association lives in the event bytecode. Unknown
whether translating the main chunk orphans the ruby cleanly or paints stray
kana — **defer such recs** until one is emulator-tested; do NOT translate the
kana tails as content (rec 46/47's lone 'れんしゅう'→'Entraînement' was a real
menu label, a different case).

**New names, 6th session 2026-07-23 (all in the glossary with evidence):**
ゴーシュ=**Gauche** 🔤 (Little Gigant striker), マーク（一之瀬の仲間）=
**Kruger** ⚠️ (Mark Kruger, SURNAME ONLY in dialogue — avoids collision with
Mark Evans; the fan-club rec 1307 uses the full "Mark Kruger"), ウィンド=
**'wind'... le vent** wordplay ⚠️ (rec 435), 山オヤジ=**le Vieux de la
Montagne** (Shawn's bear rival), ヤマネコスタジアム=**le stade du Lynx** 🔤,
角馬くん=**Chester** ⚠️ (EU canon, announcer's son), おヨネばあちゃん=
**mamie Yone** 🔤, ピョン太=**Pyonta** 🔤 (rabbit, tic **pyon**), ベリーズ=
**les Berryz** 🔤 (idols 'Cap'/'Peachichi'/'Rishako'/'Miya'), 真・帝国=
**la nouvelle Royal Académie**, 魔王=**le Roi des enfers** (matches
魔界=enfers), 長老=**l'ancien** (Lioccot lore). Reused-verbatim finds:
「さいごのノート」=**'Coeur(s)'** (rec 354 precedent — NOT "manuel"!),
équipe K / stade Tortue / stade Condor / King of Fantasista / Spark &
Bomber / Rairaiken all FR-attested. System coins: 入団テスト=**test
d'admission** (FR-attested r469), イナズマ２=**Inazuma (Eleven) 2**,
【２→３プレミアム…】=**[Recrutement/Objets premium 2-3]**, つうしんチーム=
**l'équipe d'échange (16)**, ＧＰ joke=**'points de vitalité'**.

**New names, 5th session (all in the glossary with evidence):**
ロニージョ=**Robingo** ✅ (FR ×84; his ボーイ tic = **boy/boys** kept in English,
FR-attested), 財前総理=**le Premier ministre Zaizen** ✅ (upgraded, FR ×4),
ケイン大統領=**le président américain Kane** 🔤, アラヤ・ダイスケ=**coach
Araya**/Daisuke ✅, 強化人間=**humain amélioré** ⚠️, and the bonus-arc IE GO cast:
松風天馬=**Arion Sherwind** ⚠️ (EU canon; 天パー tease → "Arion Bouclette"),
空野葵=**Skie Blue** ⚠️, 如月まこ=**Mako Kisaragi** 🔤, サスケ=**Sasuke** 🔤,
稲妻ＫＦＣ=**l'Inazuma KFC** 🔤, ブラージ=**Blasi** 🔤 (Fidio's teammate),
ロココの師匠=**maître**/**disciple** ✅, 世界一 (Rococo arc)=**numéro un
mondial** ✅. Reminders honoured: Rushe says **grand frère (Fidio)** / **tonton
K**; island is spelled **Lioccot** (FR ×75, NOT "Liocott"); scene-setting cards
use the `- Quelques mois plus tôt -` dash style; 世宇子=Kirkwood, オルフェウス=
**Orphée** (brackets only in announcer set-pieces).

**⚠️ NAME CORRECTIONS (2026-07-22, 2nd session) — six long-standing romaji
fallbacks were WRONG; the EU names were in the shipped FR all along** (the
earlier scans grepped for the romaji instead of the EU names). All artifacts
(evet.json, unitbase.json, item.json) are already fixed; the glossary rows are
updated. **Use these:** 虎丸→**Austin** (Hobbs), 飛鷹→**Thor** (Stoutberg — the
"Toby" epithet reading was wrong), 不動→**Caleb** (Stonewall), 土方→**Archer**
(Hawkins), 久遠監督→**coach Travis** (he is Camelia's father — "Percy Travis est
mon père"), フユッペ→**Camillou**, メガネ→**Willy** (Glass), 夕香→**Julia**,
佐久間→**David Samford** (the old "佐久間→Caleb" note below was a
misattribution — Caleb is 不動). **Lesson: when a character has a plausible EU
name, grep the FR corpus for the EU candidates too, not just the romaji, before
declaring "no attestation".**

**SCOPE DECISION MADE (2026-07-22): story-critical subset first.** Walk rec order
(≈ story order), translate substantive story-cutscene recs, and **skip/defer**:
recruitment scenes (386 recs / 3,248 chunks, tell: `%s rejoint l'équipe!` /
`Bonne recherche!` scaffolding), the NPC/tutorial/shop flavor band recs
1500–2100 (365 recs / 678 chunks), and short one-liner recs (<8 todo chunks).
Story spine ≈ **480 recs / ~10,500 chunks**. Signal work: a rec is side content
if its FR chunks carry recruitment scaffolding, or it's a 1–2-chunk NPC line.
Verify per rec by reading it (needed anyway).

**Resume at rec 2184.** Done through rec 2183 (story spine; sub-8-chunk recs in
between remain deferred). Deferred: 101–102,
114–123, 133, 137–144, the 165–286 NPC band, and the 288–333 one-liner band.
New names this session (all in the glossary with evidence): 鬼瓦=**détective
Smith** ✅, ミスターＫ=**Mister K** (aligned with item 962 — never "M.K"),
テレス=**Torres** ✅ (corrected from "Teres" — he's Thiago Torres, Argentina's
captain), ルシェ=**Rushe** 🔤, バダップ・スリード=**Baddap Sleed** 🔤,
栗松=**Tim Saunders** ⚠️ (EU canon; NB his letter uses でやんす — the tic is NOT
unique to Willy), ヘンクタッカー=**Hentacker** ✅ (FR-attested rec 409),
影山東吾=**Tougo Dark** 🔤, ガルシルド=**Zoolan** ✅ ⚠️**BIG CORRECTION**: the
shipped FR renames Garshield to Zoolan (×41, "Garshield" 0× in corpus; the old
ズーラン glossary row was this same character) — 40 uses across
evet/unitbase/item artifacts all fixed, full name ガルシルド・ベイハン=**Zoolan
Bayhan** 🔤, stadiums **Hydre/Paon/Titanesque** ✅
+ **Condor** ⚠️, teams **Rose Griffon**/**Little Gigant** 🔤, notebook titles
**'Dernier manuel de David'** ✅ / **'Manuel des super techniques de David'** ⚠️,
tactic 無敵の槍=**la Lance invincible** ⚠️, 影山総帥=**Commandant Dark** ✅,
ヒデナカタ=just **Hiden** ✅ (corpus never says "Nakata").
Name notes: 瞳子=**Hitomiko**, 砂木沼=**Saginuma**/**Desarm**, 秘伝書=**livre secret**
(evet), 鉄塔=**la tour**, フィディオ=**Fidio**/オルフェウス=**[Orphée]**.
(塔子/音無 resolved: 音無=Celia, 塔子=Touko.) New this session (see glossary):
ヒデ=**Hiden** (FR-attested, NOT "Hide"), 涼野=**Bryce Withingale** ⚠️,
南雲=**Claude Beacons** ⚠️, チェ・チャンスウ=**Choi Chang Soo** 🔤,
バウゼン=**Bauzen** 🔤, アストロブレイク=**la Frappe astrale** ⚠️ (matches
FR-attested アストロゲート=**la Porte astrale**), タイガードライブ=**la Frappe du
tigre** ⚠️, 爆熱ストーム=**la Tempête de feu** ⚠️, サンダービースト=**la Bête du
tonnerre** ✅, 豪炎寺の父=**Docteur Blaze**, フク=**Fuku** 🔤 (gouvernante).

### The loop, exactly

```bash
cd /home/mcpeace/ie3Ogres-rom-FR/tools && source venv/bin/activate

# 1. See what's next. As of end-of-7th-session the sub-8 pass is DONE and this
#    script prints an EMPTY pile (deferred bands + recruitment are still
#    filtered out). To start the deferred bands, remove the 101–151/165–333/
#    288–333/1500–2100 ranges from DEFERRED below (keep {962,964,972,975,979}|
#    {407} and the recruitment filter) and re-run.
python3 - <<'EOF'
import json,re
from collections import defaultdict
d=json.load(open('../translations/evet.json'))
recs=defaultdict(list)
for e in d['entries']: recs[e['rec']].append(e)
jp={}; recruit=set()
for r,es in recs.items():
    todo=sum(1 for e in es if e['cls']=='jp' and not e.get('fr') and e['src'].strip())
    if todo: jp[r]=todo
    frtxt=' '.join(e['src'] for e in es if e['cls'] in ('fr','ascii'))
    if re.search(r"rejoint l'équipe|Bonne recherche|vous rejoint",frtxt): recruit.add(r)
DEFERRED=(set(range(101,152))|set(range(165,287))|set(range(288,334))  # side content, do 2nd
          |set(range(1500,2101))                # NPC/tutorial band, do 2nd
          |{962,964,972,975,979}                # furigana-ruby recs, see note
          |{407})                               # only residue left (p41), never translate
sub=[r for r in sorted(jp) if r not in DEFERRED and r not in recruit]
print(f'pile: {len(sub)} recs / {sum(jp[r] for r in sub)} chunks; resume at rec {sub[0]}')
n=sub[:15]; print([(r,jp[r]) for r in n],'=',sum(jp[r] for r in n),'chunks')
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
吹雪→**Shawn**, 佐久間→**David Samford** *(corrected — Caleb is 不動)*,
立向居→**Darren**, 木暮→**Scotty**, 塔子→**Touko** *(NOT Celia — see glossary; 音無=Celia)*,
木野→**Silvia**, 一之瀬→**Erik Eagles** *(plural — the ROM writes it that way)*,
土門→**Bobby**, 壁山→**Jack**, 綱海→**Hurley**, ヒロト→**Xavier**, 緑川→**Jordan**,
染岡→**Kevin**, 音無（春奈）→**Celia**, 雷門夏未→**Nelly**, 木野→**Silvia**,
冬花→**Camelia** *(not a transliteration)*,
響木→**Coach Hillman**, イナズマジャパン→**Inazuma Japon** (plain — 657× in FR;
brackets only in the rare set-piece "L'[Inazuma Japon!]"). ミスター・エンドウ→
**Monsieur Evans** (surname Evans, FR ×57). ヒビキ提督→**l'amiral Hillman** (FR-attested).
Romaji fallbacks (no ROM attestation, re-checked against EU names 2026-07-22):
Rika, Touko, Suzume, Karasu, Nice Dolphin, Manyuji, Hakuren, Bauzen, Fuku.
*(Toby/Toramaru/Fudou/Hijikata/Megane/Kuon were dropped from this list — they DO
have FR attestations: Thor/Austin/Caleb/Archer/Willy/Travis, see the corrections
block above.)* Techniques get **translated**, not transliterated:
ゴッドハンド→"Main céleste" (shipped), so ザ・ウォール→**"Le Mur"**.

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

**5. Gate + reinsert-verify — after EVERY batch:**

```bash
python3 evet_fit.py ../translations/evet.json          # budget gate, MUST pass
python3 evet_reinsert.py ../translations/evet.json --out /tmp/evet_new.pkb
stat -c%s /tmp/evet_new.pkb                            # MUST print 2926480
```

**6. Full ROM repack + deploy — only when building a playable ROM for Phil**
(NOT per batch; he plays/QAs once everything is translated):

```bash
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
- **A rec's own FR chunks outrank the glossary.** The Zoolan correction was
  caught because rec 369 carried the shipped chunk "Le manoir de Zoolan est à
  présent disponible!" while the glossary said "Garshield". When an
  already-French chunk *inside the rec you're translating* names a
  person/place/team, that is the ground truth — grep the corpus for it and fix
  the glossary if they disagree. (Same pattern earlier: イタリア街="l'aire de
  l'Italie" came from rec 334's own p79.)
- **`『』` are NOT encodable in evet** (`ie3_codec` raises). When dialogue quotes
  an item title that item.STR renders as `『Cran Acharné』`, use straight quotes
  `'Cran Acharné'` — same wording, different quoting. Test odd characters with
  `ie3_codec.encode_text` *before* batching (`°` is fine, `『』` is not).
- **When dialogue quotes game items, reuse the artifact wording verbatim.** The
  11 "Coeur n°N" maxims (rec 354, re-quoted in 379/383) copy
  `translations/item.json` entries 52–62 word for word — never re-translate a
  string the player also sees as an item/menu.
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

### Working preferences (from Phil — respect these)

- **NO STORY SPOILERS in progress reports.** Phil will *play* the finished ROM.
  Report only: chunk counts / %, rec numbers done, the reinsert invariants, and
  name/glossary decisions. Never summarize what happens in the scenes, name plot
  events, or recap arcs. This also applies to what you write in project docs
  where feasible — keep rec descriptions neutral ("rec 152, 44 chunks"), not
  narrative. (Translate normally; the constraint is only on what's *said/written
  about* the content.)
- **Do NOT offer emulator spot-checks or test-ROM builds each batch.** Phil does
  the in-game QA himself by playing once everything is translated. The reinsert
  invariants (0 skipped, exact byte size) are sufficient verification during the
  work.
- ~~**The scope decision**~~ ✅ **made 2026-07-22: story-critical subset first**
  (see the SCOPE DECISION block above). Don't re-raise it.

### Still owed

- **The unitbase gender sweep, 53 entries** (`"gender_check": true` flags in
  `translations/unitbase.json`, list with `python3 tools/flag_gender.py --list`).
  Needs in-game portraits — since Phil does the in-game QA himself, the practical
  path is: leave the flags in place, and fix any wrong agreements he reports
  from his playthrough (isolated one-line edits).

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
- **`evet.pkb`: 🔶 in progress — 12,586/15,742 (80%)** (see the "NEXT SESSION"
  section at the top; that's the live loop). Budget-checked, unlike `.STR` —
  expect to tighten wording; `evet_fit.py` is the gate. NB some banter-pool
  chunks have tiny budgets (r2646 p23 was 25 bytes) — keep 1-line JP → short FR.
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
   SELECT). Note (2026-07-22): per-batch emulator eyeballing is **not** the
   workflow anymore — Phil QAs in-game himself at the end (see Working
   preferences). The debug-ROM setup stays documented for one-off format checks.
3. ~~**`.STR` dump/reinsert tools**~~ ✅ **done** — `str_slots.py` /
   `str_dump.py` / `str_reinsert.py`, byte-exact on all 7 `.STR` files.
   Correction learned while building: 32-byte alignment is a *per-file
   convention*, not universal (`games.STR` packs some strings tight), so the
   model captures actual padding. Workflow: `str_dump.py item --jp-only` → edit
   `fr` → `str_reinsert.py` → `repack_rom.py -r data_iz/logic/item.STR=…`.

With extraction, reinsertion, and repack all built for both text formats, the
project is **tooling-complete for translation**: the only remaining work is the
French drafting itself (the evet loop at the top of this file). Final QA is
Phil playing the finished ROM — not per-batch emulator checks.

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
- **The translation artifacts live in `translations/*.json`** — `evet.json` is
  the master evet artifact (all 39,610 entries, accumulates across sessions).
  Make sure they're committed/pushed before switching machines; losing
  `evet.json` loses all evet progress.
- The bypass-permission settings live in `~/.claude/settings.local.json` on the
  current machine only — not part of the project; re-add on the new machine if
  wanted.
