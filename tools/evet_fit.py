"""Pre-flight budget gate for evet translations.

Reports which edits won't fit BEFORE running evet_reinsert.py. Uses the real
Slot.set_chunk_bytes() so the verdict matches the reinsert tool exactly rather
than re-deriving the rule (growth is absorbed by zero-runs at/after the edited
part, each keeping 1 terminator zero -- it cannot borrow padding from earlier
parts, so a per-slot "total <= budget" model is NOT equivalent).

Usage: python3 evet_fit.py ../translations/evet.json
"""
import json, sys
sys.path.insert(0, '/home/mcpeace/ie3Ogres-rom-FR/tools')
from evet_slots import load_slots
from ie3_codec import encode_text

D = '/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/'

def main():
    doc = json.load(open(sys.argv[1], encoding='utf-8'))
    pkh, pkb, recs, slots = load_slots(doc['file'], D)   # fresh, disposable copy
    bad, n = [], 0
    for e in doc['entries']:
        fr = e.get('fr', '')
        if not fr or (e['cls'] != 'jp' and fr == e.get('src', '')):
            continue
        n += 1
        rid, off, bud, slot = slots[e['rec']]
        try:
            enc, _folds = encode_text(fr)
        except ValueError as ex:
            bad.append((e['rec'], e['part'], f'encode failed: {ex}')); continue
        new = bytes([int(e['lead'], 16)]) + enc
        old = len(slot.parts[e['part']][0])
        if not slot.set_chunk_bytes(e['part'], new):
            bad.append((e['rec'], e['part'], f'too long by ~{len(new)-old} B '
                                             f'(chunk {old} -> {len(new)})'))
    if bad:
        print(f'{len(bad)} of {n} edit(s) will NOT fit:')
        for rec, part, msg in bad:
            print(f'  rec{rec} part{part}: {msg}')
        sys.exit(1)
    print(f'all {n} edits fit')

main()
