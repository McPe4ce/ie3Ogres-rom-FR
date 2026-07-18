"""Custom single-byte French text codec for Inazuma Eleven 3 (Ogre) FR patch.

DERIVED & CONFIRMED 2026-07-18 from cleanly .pkh-bounded evet French chunks
(11,264) cross-checked against mcht (465) — both use the identical accented-
letter set. See docs/FORMAT_NOTES.md and the ie3-french-encoding skill.

Model of a text run inside a .pkb sub-string:
  - 0x20..0x7E  : standard ASCII (letters, digits, punctuation, space)
  - 0x0A        : newline
  - high bytes  : the custom accents below (single byte each)
  - 0x81 <t>    : leftover full-width SJIS symbols (two bytes), rendered as-is
  - other <0x20 / unmapped high bytes : opaque CONTROL codes (box style, text
                  speed, etc.) — preserved verbatim, never "translated".
Japanese (untranslated) runs use standard 2-byte Shift-JIS and are handled by
the caller (detect per run); this codec is for the custom FR scheme.
"""

# --- confirmed custom single-byte accents (byte -> char) ---
DECODE_HI = {
    0xB1: "à", 0xB3: "â", 0xB8: "ç", 0xB9: "è", 0xBA: "é",
    0xBB: "ê", 0xBF: "î", 0xC0: "ï", 0xC5: "ô", 0xC9: "ù", 0xCB: "û",
}
# --- confirmed 0x81-prefixed full-width symbols (trail byte -> char) ---
DECODE_81 = {0x8B: "°", 0x99: "☆", 0xF4: "♪", 0x63: "…"}

ENCODE_HI = {v: k for k, v in DECODE_HI.items()}
ENCODE_81 = {v: bytes([0x81, k]) for k, v in DECODE_81.items()}

# House-style folding for characters the shipped translation never used a
# dedicated byte for (uppercase accents other than Ù, rare accents, ligatures,
# guillemets). The existing FR text writes capitals unaccented and uses ASCII
# oe/ae and straight quotes. encode_text() applies these so a translator can
# type natural French and still get valid, house-consistent bytes; it reports
# which folds happened so nothing is lost silently.
FOLD = {
    "É": "E", "È": "E", "Ê": "E", "Ë": "E", "À": "A", "Â": "A", "Ä": "A",
    "Î": "I", "Ï": "I", "Ô": "O", "Ö": "O", "Û": "U", "Ü": "U", "Ç": "C",
    "Ù": "U",  # only lowercase ù (0xC9) is in the corpus; uppercase folds
    "ë": "e", "ä": "a", "ö": "o", "ü": "u",
    "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE",
    "«": '"', "»": '"', "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...",  # note: … also has SJIS form (0x81 63)
}


def decode_text(raw: bytes, control="token") -> str:
    """Decode a custom-FR byte run to a str.
    control="token": unmapped control/high bytes shown as <XX> and 0x81-pairs
      as their symbol; use for human display/inspection.
    control="strip": drop control bytes < 0x20 (except newline)."""
    out = []
    i, n = 0, len(raw)
    while i < n:
        c = raw[i]
        if c == 0x81 and i + 1 < n and raw[i + 1] in DECODE_81:
            out.append(DECODE_81[raw[i + 1]]); i += 2; continue
        if 0x20 <= c < 0x7f:
            out.append(chr(c))
        elif c == 0x0a:
            out.append("\n")
        elif c in DECODE_HI:
            out.append(DECODE_HI[c])
        else:
            if control == "token":
                out.append(f"<{c:02X}>")
            # strip: skip
        i += 1
    return "".join(out)


import re
_TOKEN = re.compile(r"<([0-9A-Fa-f]{2})>")

def encode_text(s: str):
    """Encode a French str to custom-FR bytes. Returns (data, folds) where
    folds is a list of (char, replacement) applied via FOLD. Raises
    ValueError on a character that can neither be encoded nor folded.

    A literal control byte can be written as a `<XX>` token (hex), which
    encodes back to that raw byte — this makes decode_text(control="token")
    fully round-trippable, so any chunk can be edited as text and re-encoded
    byte-exactly. To write a literal '<', use `<3C>`."""
    out = bytearray()
    folds = []
    i, n = 0, len(s)
    while i < n:
        m = _TOKEN.match(s, i)
        if m:
            out.append(int(m.group(1), 16)); i = m.end(); continue
        ch = s[i]; i += 1
        if ch == "\n":
            out.append(0x0a); continue
        o = ord(ch)
        if 0x20 <= o < 0x7f:
            out.append(o); continue
        if ch in ENCODE_HI:
            out.append(ENCODE_HI[ch]); continue
        if ch in ENCODE_81:
            out += ENCODE_81[ch]; continue
        if ch in FOLD:
            rep = FOLD[ch]; folds.append((ch, rep))
            sub, sub_folds = encode_text(rep)
            out += sub; folds += sub_folds; continue
        raise ValueError(f"cannot encode char {ch!r} (U+{o:04X})")
    return bytes(out), folds


# quick self-test / round-trip check when run directly
if __name__ == "__main__":
    samples = [
        " Où veux-tu aller? ",
        "Aller à la carte? ",
        "C'est une très bonne idée.\nSortons déjà d'ici!",
        "Il faut peut-être se dépêcher, garçon.",
        "égoïste, naïf, sûr, hâte, bientôt, connaître",
    ]
    for s in samples:
        data, folds = encode_text(s)
        back = decode_text(data)
        ok = back == s
        print(f"{'OK ' if ok else 'DIFF'} {s!r}")
        if not ok:
            print(f"      -> {back!r}")
        if folds:
            print(f"      folds: {folds}")
