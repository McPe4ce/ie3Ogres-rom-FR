#!/usr/bin/env python3
"""Mark unitbase entries whose JP is gender-neutral but whose FR had to pick one.

Adds "gender_check": true to the given indices in translations/unitbase.json.
Durable (lives in the artifact), machine-readable, and trivially removable:
    python3 flag_gender.py --list      # show all flagged
    python3 flag_gender.py 1319 1368   # flag these
"""
import json, sys

OUT = '/home/mcpeace/ie3Ogres-rom-FR/translations/unitbase.json'
d = json.load(open(OUT))
by_idx = {e['idx']: e for e in d['entries']}

if '--list' in sys.argv:
    flagged = [e for e in d['entries'] if e.get('gender_check')]
    print(f'{len(flagged)} entries flagged for gender review:')
    for e in flagged:
        print(f"  {e['idx']}: {e['fr'].splitlines()[0]}")
    sys.exit()

idxs = [int(a) for a in sys.argv[1:]]
missing = [i for i in idxs if i not in by_idx]
if missing:
    sys.exit(f'unknown idx: {missing}')
for i in idxs:
    by_idx[i]['gender_check'] = True
json.dump(d, open(OUT, 'w'), ensure_ascii=False, indent=1)
print(f'flagged {len(idxs)}; total flagged now '
      f"{sum(1 for e in d['entries'] if e.get('gender_check'))}")
