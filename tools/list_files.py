import sys
import ndspy.rom

ROM_PATH = "/home/mcpeace/ie3Ogres-rom-FR/Inazuma-Eleven-3-Sekai-heno-Chousen-The-Ogre-DS-Traduit-en-Français-v06.nds"

rom = ndspy.rom.NintendoDSRom.fromFile(ROM_PATH)

print("Game code:", rom.idCode)
print("Name:", rom.name)
print("Number of files:", len(rom.files))
print()

def walk(folder, prefix=""):
    for name, sub in folder.folders:
        walk(sub, prefix + name + "/")
    for name in folder.files:
        print(f"{prefix}{name}")

walk(rom.filenames)
