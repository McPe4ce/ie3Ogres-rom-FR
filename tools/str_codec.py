"""Full-width SJIS text codec for .STR files (data_iz/logic/*.STR).

Unlike evet.pkb dialogue (single-byte, lowercase-accented — see ie3_codec.py),
.STR menu/description pools are rendered in **full-width SJIS Latin with NO
accents**. Verified against the already-translated pools (sp_binder, command,
tacticscmd): every French letter/digit is a full-width form, spaces are the
full-width space U+3000 (SJIS 81 40), apostrophes are the right single quote
U+2019 (SJIS 81 66), and accented letters are written unaccented (house style).

`encode_str_fr(s)` : French (ASCII, may contain accents) -> full-width SJIS bytes.
                     Accents are folded to ASCII first (é->e, à->a, ç->c, ...).
`decode_str_fr(b)` : full-width SJIS bytes -> readable ASCII French (NFKC).

Newlines (0x0A) pass through as-is. This codec is used by str_reinsert.py;
str_dump.py decodes the Japanese source separately.
"""
import unicodedata

# Accent folding (house style: .STR text carries no accents at all).
_FOLD = str.maketrans({
    "à": "a", "â": "a", "ä": "a", "á": "a",
    "è": "e", "é": "e", "ê": "e", "ë": "e",
    "î": "i", "ï": "i", "í": "i", "ì": "i",
    "ô": "o", "ö": "o", "ó": "o", "ò": "o",
    "ù": "u", "û": "u", "ü": "u", "ú": "u",
    "ç": "c", "ñ": "n",
    "À": "A", "Â": "A", "Ä": "A", "Á": "A",
    "È": "E", "É": "E", "Ê": "E", "Ë": "E",
    "Î": "I", "Ï": "I", "Ô": "O", "Ö": "O",
    "Ù": "U", "Û": "U", "Ü": "U", "Ç": "C",
    "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE",
})

# ASCII punctuation whose full-width form the game uses. Apostrophe and hyphen
# map to the typographic forms seen in the shipped text (’ and −).
_PUNCT = {
    "'": "’",   # U+2019  (SJIS 81 66)
    "-": "−",   # U+2212  minus sign, as seen in "Est−ce"
    " ": "　",  # full-width space (SJIS 81 40)
}


def _to_fullwidth(ch):
    if ch in _PUNCT:
        return _PUNCT[ch]
    o = ord(ch)
    if 0x21 <= o <= 0x7E:          # printable ASCII -> full-width (offset 0xFEE0)
        return chr(o + 0xFEE0)
    return ch                       # already full-width / newline / other


def encode_str_fr(s):
    """French string -> full-width SJIS bytes. Returns (bytes, folds) where
    folds lists (accented_char, replacement) applied, for reporting."""
    folded = s.translate(_FOLD)
    # Accurate fold report: each source char that _FOLD rewrites (length-changing
    # folds like œ→oe would misalign a naive zip of s vs folded).
    folds = [(ch, _FOLD[ord(ch)]) for ch in s if ord(ch) in _FOLD]
    out = []
    for ch in folded:
        if ch == "\n":
            out.append("\n")
        else:
            out.append(_to_fullwidth(ch))
    text = "".join(out)
    try:
        return text.encode("shift_jis"), folds
    except UnicodeEncodeError as e:
        raise ValueError(f"cannot encode to full-width SJIS: {e} in {s!r}")


def decode_str_fr(b):
    """Full-width SJIS bytes -> readable ASCII French (NFKC-normalized)."""
    return unicodedata.normalize("NFKC", b.decode("shift_jis", errors="replace"))


if __name__ == "__main__":
    # Round-trip proof against the shipped already-French .STR pools: decoding a
    # real French string and re-encoding it must reproduce the original bytes.
    from str_slots import load
    total = ok = 0
    mism = []
    for name in ("sp_binder", "command", "tacticscmd"):
        _, recs = load(name)
        for t, _p in recs:
            if not t:
                continue
            s = decode_str_fr(t)
            # skip records that are genuinely Japanese (untranslated leftovers)
            if any('぀' <= c <= 'ヿ' or '一' <= c <= '鿿'
                   for c in s):
                continue
            total += 1
            enc, _ = encode_str_fr(s)
            if enc == t:
                ok += 1
            elif len(mism) < 8:
                mism.append((name, s[:40], t[:16].hex(' '), enc[:16].hex(' ')))
    print(f"round-trip: {ok}/{total} already-French .STR records reproduce exactly")
    for nm, s, a, b in mism:
        print(f"  MISMATCH [{nm}] {s!r}\n     orig {a}\n     enc  {b}")
