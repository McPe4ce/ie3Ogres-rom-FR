import os
import ndspy.rom

ROM_PATH = "/home/mcpeace/ie3Ogres-rom-FR/Inazuma-Eleven-3-Sekai-heno-Chousen-The-Ogre-DS-Traduit-en-Français-v06.nds"
OUT_DIR = "/home/mcpeace/ie3Ogres-rom-FR/extracted"

rom = ndspy.rom.NintendoDSRom.fromFile(ROM_PATH)

def walk(folder, prefix=""):
    for name, sub in folder.folders:
        walk(sub, prefix + name + "/")
    for name in folder.files:
        idx = folder.idOf(name)
        path = os.path.join(OUT_DIR, prefix, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(rom.files[idx])

walk(rom.filenames)

# Also dump arm9/arm7 binaries and overlays, since some text/pointer tables
# can live in the main binaries rather than the filesystem.
with open(os.path.join(OUT_DIR, "_arm9.bin"), "wb") as f:
    f.write(rom.arm9)
with open(os.path.join(OUT_DIR, "_arm7.bin"), "wb") as f:
    f.write(rom.arm7)

os.makedirs(os.path.join(OUT_DIR, "_overlay9"), exist_ok=True)
for ovid, ov in rom.loadArm9Overlays().items():
    with open(os.path.join(OUT_DIR, "_overlay9", f"overlay9_{ovid:04d}.bin"), "wb") as f:
        f.write(ov.data)

print("Done extracting to", OUT_DIR)
