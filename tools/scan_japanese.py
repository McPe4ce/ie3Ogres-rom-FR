import os

ROOT = "/home/mcpeace/ie3Ogres-rom-FR/extracted"
MIN_RUN = 6  # minimum consecutive Japanese characters to report

def is_jis_lead(b):
    return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC)

def is_jis_trail(b):
    return (0x40 <= b <= 0xFC) and b != 0x7F

def is_han_kana(ch):
    o = ord(ch)
    return (
        0x3040 <= o <= 0x30FF   # hiragana + katakana
        or 0x4E00 <= o <= 0x9FFF  # CJK unified ideographs
        or 0xFF66 <= o <= 0xFF9D  # halfwidth katakana
    )

def scan_file(data):
    runs = []
    i = 0
    n = len(data)
    cur = []
    cur_start = None
    while i < n:
        b = data[i]
        matched = False
        if is_jis_lead(b) and i + 1 < n and is_jis_trail(data[i+1]):
            try:
                ch = bytes([b, data[i+1]]).decode("shift_jis")
            except UnicodeDecodeError:
                ch = None
            if ch is not None and is_han_kana(ch):
                if cur_start is None:
                    cur_start = i
                cur.append(ch)
                i += 2
                matched = True
        if not matched:
            if cur_start is not None:
                if len(cur) >= MIN_RUN:
                    runs.append((cur_start, "".join(cur)))
                cur = []
                cur_start = None
            i += 1
    if cur_start is not None and len(cur) >= MIN_RUN:
        runs.append((cur_start, "".join(cur)))
    return runs

results = {}
total_files = 0
for dirpath, _, filenames in os.walk(ROOT):
    for fn in filenames:
        path = os.path.join(dirpath, fn)
        total_files += 1
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            continue
        runs = scan_file(data)
        if runs:
            results[path] = runs

print(f"Scanned {total_files} files, found Japanese text in {len(results)} files\n")

# Sort by number of runs descending, most interesting files first
for path, runs in sorted(results.items(), key=lambda kv: -len(kv[1])):
    rel = os.path.relpath(path, ROOT)
    print(f"=== {rel}  ({len(runs)} runs) ===")
    for offset, text in runs[:5]:
        preview = text[:40].replace("\n", "\\n")
        print(f"  0x{offset:08X}: {preview}")
    if len(runs) > 5:
        print(f"  ... and {len(runs) - 5} more")
    print()
