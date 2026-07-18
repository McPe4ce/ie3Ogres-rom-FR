# How it works — a beginner's explainer

A plain-language walkthrough of what the `.pkb`/`.pkh` dialogue format is, how
the game finds a line of text, and where that text actually lives. Written for
someone new to ROM hacking. For the precise byte layout see
[`FORMAT_NOTES.md`](FORMAT_NOTES.md); this file is the intuition.

---

## 1. The problem the format solves

The game has ~3,000 chunks of story dialogue, all different lengths. Two things
have to happen:

1. When you reach a point in the story, the game's code must **find** the right
   line of dialogue.
2. That text has to be **stored** somewhere on the cartridge.

Dumping everything into one big file would force the code to *search* for a
line every time — slow and fragile. So the format uses a pattern you see
everywhere in computing: **split it into an index and the data.** Like a book:

```
   TABLE OF CONTENTS              THE PAGES
   ┌────────────────────┐        ┌────────────────────┐
   │ Chapter 5 ... p.210│───────▶│ (page 210)         │
   │ Chapter 6 ... p.244│        │  actual text here  │
   └────────────────────┘        └────────────────────┘
     small, quick to scan          big, holds content
```

That is exactly what the two files are:

| File | Role | Analogy | Size (evet) |
|------|------|---------|-------------|
| **`evet.pkh`** | the **index** ("**p**ac**k** **h**eader") | table of contents | 35 KB |
| **`evet.pkb`** | the **body** ("**p**ac**k** **b**lob") | the pages | 2.9 MB |

---

## 2. What a "slot" is

The `.pkh` index is a list of 2,972 entries. Each entry is just **three
numbers** (12 bytes):

```
record 0:  ID = 0x01D92CD0     offset = 0        budget = 372
           │                   │                 │
           │ a label the       │ "the text is    │ "it may be up to
           │ game's code        │  at byte 0 of   │  372 bytes long"
           │ asks for           │  evet.pkb"      │
```

- **ID** — a label. The game's *script* asks for dialogue by this ID, never by
  a raw address. You never change it.
- **offset** — *where* in the big `.pkb` this text starts.
- **budget** — *how much room* is reserved for it.

**A "slot" is that reserved region of the `.pkb`.** Think of a **parking
space**: the text parks there, and `budget` is the size of the space.

```
   evet.pkb  (one long file of bytes)
   ┌─────────┬───────────┬───────────┬──────────── ...
   │ slot 0  │  slot 1   │  slot 2   │
   │ 372 B   │  372 B    │  372 B    │
   └─────────┴───────────┴───────────┴──────────── ...
   ▲         ▲           ▲
   offset 0  offset 384  offset 768
```

This is the single most important idea, and it's the rule that constrains us:
**a translation has to fit inside its parking space.**

> Note: the gap between one slot's `budget` end and the next slot's `offset`
> (e.g. bytes 372–383) is filler bytes `04 FF FF…`, not part of either slot.

---

## 3. What's inside one slot

Here is the **real** content of slot 0 of `evet.pkb`. It isn't one string — it's
a little menu of dialogue choices:

```
 slot-byte
 ┌────┐
 │  3 │  " O·veux-tu aller? "      → "Où veux-tu aller?"   (· = 0xC9 = ù)
 │ 35 │  04                        → a control code (not text)
 │ 39 │  "<Aller · la carte? "     → "Aller à la carte?"   (· = 0xB1 = à)
 │ 99 │  04                        → control code
 │107 │  "dPasser par ici?⏎Ce n'est pas ouvert."
 │ .. │  ...
 └────┘
   (the spaces between are runs of 00 bytes = padding + string terminators)
```

Four things to notice, all real:

1. **Multiple sub-strings per slot** — one slot packs all the options of a
   choice menu together.
2. **A `00` byte ends each string** (a "terminator" — the computer's full
   stop). Leftover `00`s are just empty padding filling the slot.
3. **Control codes** — the lone `04` bytes are instructions to the text engine
   (e.g. "next option"), not letters. The first character of each string
   (`<`, `d`, the leading space) is a **box/speaker control code** too. We keep
   these exactly and never translate them.
4. **The custom encoding** — `0xC9` is `ù` and `0xB1` is `à`. A normal computer
   would read `0xC9` as `É`; this game doesn't. Cracking that table is what
   `tools/ie3_codec.py` is for.

---

## 4. Where the text actually lives — three nested "dolls"

"Address" can mean three different things here, like Russian dolls. Two we work
with directly; the third only exists while the game runs.

```
  ┌─────────────────────────────────────────────────────────────┐
  │ DOLL 3:  Console RAM (only while playing)                    │
  │  the game copies the text into memory at e.g. 0x02135A80     │
  │  ── we do NOT have this; needs an emulator debugger ──       │
  │   ┌───────────────────────────────────────────────────────┐ │
  │   │ DOLL 2:  Inside the .nds ROM filesystem (NitroFS)      │ │
  │   │  evet.pkb sits at some byte N inside the cartridge     │ │
  │   │  (our `extracted/` folder is this doll, unpacked)      │ │
  │   │   ┌─────────────────────────────────────────────────┐ │ │
  │   │   │ DOLL 1:  Byte offset INSIDE evet.pkb            │ │ │
  │   │   │  "Aller à la carte?" is at byte 39             │ │ │
  │   │   │  ── this is where all our tools work ──        │ │ │
  │   │   └─────────────────────────────────────────────────┘ │ │
  │   └───────────────────────────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────┘
```

**Doll 1 — offset inside `evet.pkb`** (what we use). The `.pkh` index hands out
these. `"Aller à la carte?"` is at **byte 39**: the slot starts at offset 0 and
the sub-string sits 39 bytes in → `0 + 39 = 39`. You can `seek(39)` and read it
directly, no searching. That addition *is* the entire lookup.

**Doll 2 — where `evet.pkb` sits in the ROM.** On the cartridge, `evet.pkb` is
packed inside the ROM's own filesystem (which is *also* an index+data
structure). When we ran `extract_rom.py`, the `ndspy` library unpacked that
filesystem to disk — that's why you have `extracted/data_iz/script/evet.pkb` as
a real file you can open. The text is never stored as readable text anywhere;
it's raw bytes inside that `.pkb`. Our JSON dump (`evet_dump.py`) is the first
time it becomes human-readable.

**Doll 3 — console RAM while playing** (we do NOT have this). When you play, the
DS copies the text from the cartridge into working memory, where it gets a live
address like `0x02135A80`. That address only exists while running, differs every
time, and needs an emulator's debugger to see. **We never need it** — we edit
the file *before* it runs; the console loads *our* bytes into RAM for us.

---

## 5. "What address is given each time a string is called?"

The subtle, important bit: **the game's script never hardcodes an address.** It
asks by **ID**, and the address is looked up fresh from the index every time.

```
   script code:   "show dialogue 0x01D92CD0"
                          │
                          ▼
   .pkh INDEX:    look up 0x01D92CD0  →  offset = 0, budget = 372
                          │
                          ▼
   .pkb DATA:     read the text starting at offset 0
```

That indirection is exactly why editing is safe: the script only ever knew the
**ID**, not the address. As long as each ID still points at the right slot and
the new text fits the budget, we can rewrite the bytes freely and the game still
finds them.

> The same question decided how safe the `.STR` files are to edit. There the
> game looks strings up by **position/count** (the Nth string) rather than a
> stored address — also indirection, also safe. See `FORMAT_NOTES.md`.

---

## 6. How our tools map onto all this

Translating one line, start to finish:

```
  ┌──────────────┐   read the index, get every slot's offset+budget
  │ evet_slots.py│   and model each slot as exact bytes (loss-free)
  └──────┬───────┘
         ▼
  ┌──────────────┐   split each slot into sub-strings, skip control codes,
  │ evet_dump.py │   decode text (Japanese via Shift-JIS, French via our table)
  └──────┬───────┘   → writes an editable JSON
         ▼
     ✎ you edit the "fr" field with the French translation
         ▼
  ┌──────────────┐   re-encode the French to game bytes, drop it back into the
  │evet_reinsert │   slot (keeping control codes, using the padding as growing
  │    .py       │   room), check it still fits the budget → writes a new .pkb
  └──────────────┘
         ▼
     (later) repack the new .pkb into the .nds and test in an emulator
```

The whole thing rests on one guarantee I proved first: **dump a slot and put it
back unchanged, and the `.pkb` comes out byte-for-byte identical.** If that
holds, the tool understands the format correctly and won't silently corrupt a
control code or break the game's ability to find the next slot. Only after that
did the tools start making real edits.

The text encoding/decoding itself is `tools/ie3_codec.py`; the confirmed
byte↔character table lives there and in `FORMAT_NOTES.md`.
