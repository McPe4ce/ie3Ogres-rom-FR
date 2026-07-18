"""Byte-exact slot model for evet.pkb (and any .pkb/.pkh text pair).

A slot (the pkb bytes for one .pkh record) is modeled as:
    leading_zeros, then a sequence of (chunk_bytes, zeros_after)
where a "chunk" is a maximal run of non-zero bytes and zeros_after is the run
of 0x00 that follows it (padding + the string terminator). Concatenating
    0x00*leading_zeros + for each (chunk + 0x00*zeros_after)
reproduces the slot EXACTLY, so the model is loss-free.

Editing a text chunk grows/shrinks chunk_bytes and compensates by borrowing
from / returning to the following zero runs, keeping the slot's total byte
span constant so every later slot's pkh offset stays valid and the .pkh file
needs no changes.
"""
import struct
from ie3_codec import decode_text, encode_text

def read_pkh(pkh):
    assert pkh[:8] == b"PackNum ", "bad .pkh magic"
    count, = struct.unpack_from("<H", pkh, 0x16)
    return [struct.unpack_from("<III", pkh, 48 + i*12) for i in range(count)]

def sjis_cov(b):
    n = len(b)
    if not n: return 0.0
    cons = k = 0
    while k < n-1:
        lo = b[k]
        if (0x81 <= lo <= 0x9f) or (0xe0 <= lo <= 0xef):
            tr = b[k+1]
            if 0x40 <= tr <= 0xfc and tr != 0x7f:
                cons += 2; k += 2; continue
        k += 1
    return cons/n

def classify(chunk):
    if len(chunk) <= 2 and all(c < 0x20 or c >= 0x80 for c in chunk):
        return "ctrl"
    if sjis_cov(chunk) >= 0.30:
        return "jp"
    printable = sum(1 for c in chunk if 0x20 <= c < 0x7f)
    if printable >= max(2, 0.5*len(chunk)):
        return "fr" if any(c >= 0x80 for c in chunk) else "ascii"
    return "ctrl"

class Slot:
    def __init__(self, span, data):
        """span = total byte length reserved for this slot in the pkb
        (next record offset - this offset, or budget for the last)."""
        self.span = span
        self.raw = data                      # original slot bytes (len == span)
        self.lead_zeros = 0
        self.parts = []                      # list of [chunk_bytearray, zeros_after]
        self._parse(data)

    def _parse(self, data):
        i, n = 0, len(data)
        z = 0
        while i < n and data[i] == 0:
            i += 1; z += 1
        self.lead_zeros = z
        while i < n:
            j = i
            while j < n and data[j] != 0:
                j += 1
            chunk = bytearray(data[i:j])
            k = j
            while k < n and data[k] == 0:
                k += 1
            self.parts.append([chunk, k - j])
            i = k

    def recompose(self):
        out = bytearray(b"\x00" * self.lead_zeros)
        for chunk, za in self.parts:
            out += chunk
            out += b"\x00" * za
        # pad/truncate to span (should already match if lengths conserved)
        if len(out) < self.span:
            out += b"\x00" * (self.span - len(out))
        return bytes(out)

    def roundtrips(self):
        return self.recompose() == self.raw

    # --- editing ---
    def set_chunk_bytes(self, idx, new_bytes):
        """Replace part[idx]'s chunk with new_bytes, conserving total span by
        adjusting following zero-runs. Returns True on success, False if there
        isn't enough padding slack in the slot to absorb the growth."""
        old = self.parts[idx][0]
        delta = len(new_bytes) - len(old)
        self.parts[idx][0] = bytearray(new_bytes)
        if delta == 0:
            return True
        if delta < 0:
            # give the freed bytes back as padding right after this chunk
            self.parts[idx][1] += -delta
            return True
        # need `delta` more bytes: take from zero-runs at/after idx, each must
        # keep >=1 zero (string terminator) except we can also use lead? no.
        need = delta
        for p in range(idx, len(self.parts)):
            avail = self.parts[p][1] - 1  # keep 1 terminator zero
            take = min(avail, need)
            if take > 0:
                self.parts[p][1] -= take
                need -= take
            if need == 0:
                break
        if need > 0:
            # also consume trailing pad implicitly present via span padding:
            # recompute current length vs span
            cur = self.lead_zeros + sum(len(c)+za for c, za in self.parts)
            slack = self.span - cur
            if slack >= need:
                need = 0
        return need == 0


def load_slots(name="evet", dir="/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/"):
    pkh = open(dir + name + ".pkh", "rb").read()
    pkb = open(dir + name + ".pkb", "rb").read()
    recs = read_pkh(pkh)
    slots = []
    for i, (rid, off, bud) in enumerate(recs):
        # A slot owns exactly `budget` bytes at `off`; the gap up to the next
        # record's offset is inter-slot filler (0x04 0xFF...) we never touch.
        slots.append((rid, off, bud, Slot(bud, pkb[off:off+bud])))
    return pkh, pkb, recs, slots


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "evet"
    pkh, pkb, recs, slots = load_slots(name)
    bad = [i for i, (_, _, _, s) in enumerate(slots) if not s.roundtrips()]
    # also verify full-file recompose equals original pkb over the slot spans
    rebuilt = bytearray(pkb)
    for rid, off, bud, s in slots:
        rebuilt[off:off+s.span] = s.recompose()
    print(f"{name}: {len(slots)} slots")
    print(f"  per-slot roundtrip failures: {len(bad)}" + (f" e.g. {bad[:5]}" if bad else ""))
    print(f"  full-pkb identical after recompose: {bytes(rebuilt) == pkb}")
    # chunk classification tally
    from collections import Counter
    cc = Counter()
    for *_, s in slots:
        for chunk, _za in s.parts:
            cc[classify(bytes(chunk))] += 1
    print(f"  chunk classes: {dict(cc)}")
