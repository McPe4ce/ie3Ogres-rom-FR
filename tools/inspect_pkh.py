import struct

PKH = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/evet.pkh"
PKB = "/home/mcpeace/ie3Ogres-rom-FR/extracted/data_iz/script/evet.pkb"

pkh = open(PKH, "rb").read()
pkb = open(PKB, "rb").read()

print("pkh size:", len(pkh), "pkb size:", len(pkb))
magic = pkh[:16]
print("magic:", magic)

filesize, = struct.unpack_from("<I", pkh, 0x10)
print("declared filesize field @0x10:", filesize, "== len(pkh)?", filesize == len(pkh))

for h in (32, 40, 44, 48, 52, 56, 64):
    remainder_bytes = len(pkh) - h
    for rec in (8, 12, 16, 20):
        if remainder_bytes % rec == 0:
            count = remainder_bytes // rec
            print(f"header={h:3d} recsize={rec:2d} -> count={count}")
