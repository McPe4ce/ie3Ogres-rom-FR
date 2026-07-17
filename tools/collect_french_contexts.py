import os
import re
from collections import defaultdict, Counter

ROOT = "/home/mcpeace/ie3Ogres-rom-FR/extracted"

# Only look at files we've confirmed or strongly suspect hold real
# human-readable text, to avoid drowning in binary (model/audio/etc) noise.
CANDIDATES = [
    "data_iz/script/evet.pkb",
    "data_iz/script/eve.pkb",
    "data_iz/script/mcht.pkb",
    "data_iz/script/mch.pkb",
    "data_iz/script/help.pkb",
    "data_iz/script/act.pkb",
    "data_iz/script/mr.pkb",
    "data_iz/script/mrobj.pkb",
    "data_iz/script/blogpost.dat",
    "data_iz/script/blogres.dat",
    "data_iz/logic/command.STR",
    "data_iz/logic/games.STR",
    "data_iz/logic/item.STR",
    "data_iz/logic/rpgtitle.STR",
    "data_iz/logic/sp_binder.STR",
    "data_iz/logic/tacticscmd.STR",
    "data_iz/logic/unitbase.STR",
    "data_iz/pic2d/cmd/mbd_c.pkb",
    "data_iz/pic2d/cmd/tcd_c.pkb",
]

def is_candidate(path):
    rel = os.path.relpath(path, ROOT)
    return rel in CANDIDATES

# token = run of bytes in [0x20-0x7E] or [0x80-0xFF], length >= 3,
# containing at least one byte >= 0x80 (so we only look at words that
# actually need an accented char) and at least 2 ascii-letter bytes.
TOKEN_RE = re.compile(rb'[\x20-\x7E\x80-\xFF]{3,40}')

def is_jis_lead(b):
    return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC)

def is_jis_trail(b):
    return (0x40 <= b <= 0xFC) and b != 0x7F

def is_han_kana(ch):
    o = ord(ch)
    return (
        0x3040 <= o <= 0x30FF
        or 0x4E00 <= o <= 0x9FFF
        or 0xFF66 <= o <= 0xFF9D
    )

def sjis_covered_positions(tok):
    """Return set of byte indices in tok that are part of a valid SJIS
    lead/trail pair decoding to a kana/kanji character."""
    covered = set()
    i = 0
    n = len(tok)
    while i < n:
        b = tok[i]
        if is_jis_lead(b) and i + 1 < n and is_jis_trail(tok[i+1]):
            try:
                ch = bytes([b, tok[i+1]]).decode("shift_jis")
            except UnicodeDecodeError:
                ch = None
            if ch is not None and is_han_kana(ch):
                covered.add(i)
                covered.add(i+1)
                i += 2
                continue
        i += 1
    return covered

contexts = defaultdict(Counter)  # high_byte -> Counter of (context string)
byte_counts = Counter()

for dirpath, _, filenames in os.walk(ROOT):
    for fn in filenames:
        path = os.path.join(dirpath, fn)
        if not is_candidate(path):
            continue
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            continue
        for m in TOKEN_RE.finditer(data):
            tok = m.group()
            if not any(b >= 0x80 for b in tok):
                continue
            ascii_letters = sum(1 for b in tok if 0x41 <= b <= 0x7A)
            if ascii_letters < 2:
                continue
            jis_covered = sjis_covered_positions(tok)
            for i, b in enumerate(tok):
                if b >= 0x80 and i not in jis_covered:
                    byte_counts[b] += 1
                    # build a readable context: ascii as-is, other high bytes as [XX], this byte as {byte}
                    ctx = []
                    for j, b2 in enumerate(tok):
                        if 0x20 <= b2 <= 0x7E:
                            ctx.append(chr(b2))
                        elif j == i:
                            ctx.append("{" + f"{b2:02X}" + "}")
                        else:
                            ctx.append(f"[{b2:02X}]")
                    contexts[b][("".join(ctx))] += 1

print("High-byte frequency (top 40):")
for b, c in byte_counts.most_common(40):
    print(f"  0x{b:02X}: {c}")

print()
for b, c in byte_counts.most_common(25):
    print(f"=== 0x{b:02X} (n={c}) ===")
    for ctx, cnt in contexts[b].most_common(8):
        print(f"    {cnt:4d}  {ctx}")
    print()
