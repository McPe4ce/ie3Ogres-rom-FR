import struct

PKH = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/evet.pkh"
PKB = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/evet.pkb"

pkh = open(PKH, "rb").read()
pkb = open(PKB, "rb").read()

HEADER = 48
RECSIZE = 12
count, = struct.unpack_from("<H", pkh, 0x16)
print("record count from header:", count)

records = []
for i in range(count):
    off = HEADER + i * RECSIZE
    a, b, c = struct.unpack_from("<III", pkh, off)
    records.append((a, b, c))

# Find real entry boundaries in pkb: entries start right after a run of
# zero-padding and consist of a small binary prefix then bytes until 0x00.
def find_entries(data, max_entries=20):
    entries = []
    i = 0
    n = len(data)
    while i < n and len(entries) < max_entries:
        # skip zero padding
        while i < n and data[i] == 0:
            i += 1
        if i >= n:
            break
        start = i
        # advance to next 0x00 terminator (this is the raw record, prefix+text)
        j = i
        while j < n and data[j] != 0:
            j += 1
        entries.append((start, j))
        i = j
    return entries

entries = find_entries(pkb, max_entries=15)
print("\nFirst raw pkb entries (start,end) by null-padding scan:")
for s, e in entries:
    print(f"  0x{s:06X} - 0x{e:06X}  len={e-s}  bytes={pkb[s:min(e,s+20)]!r}")

print("\nFirst 15 pkh records (A, B, C):")
for a, b, c in records[:15]:
    print(f"  A=0x{a:08X} ({a})  B=0x{b:08X} ({b})  C=0x{c:08X} ({c})")

# Check deltas
print("\nDeltas between consecutive records:")
for i in range(1, 15):
    da = records[i][0] - records[i-1][0]
    db = records[i][1] - records[i-1][1]
    dc = records[i][2] - records[i-1][2]
    print(f"  dA={da} dB={db} dC={dc}")
