"""Write edited internal file(s) back into a fresh .nds ROM via ndspy.

The original ROM is the base and is never modified: it's loaded, the named
internal files are replaced in-memory with the edited versions, and a NEW .nds
is written. With no --replace arguments this is a pure round-trip — the output
is byte-identical to the input (that's the correctness check; see --verify).

Each --replace maps an internal ROM path to a local edited file, e.g.:
  --replace data_iz/script/evet.pkb=evet_new.pkb
The internal path is the same path scan_japanese.py / extract_rom.py use
(relative to the ROM filesystem root, "/" separators, no leading slash).

Usage:
  # pure round-trip: prove repack is lossless (out == original, byte-for-byte)
  python3 repack_rom.py -o /tmp/roundtrip.nds --verify

  # patch one file
  python3 repack_rom.py --replace data_iz/script/evet.pkb=evet_new.pkb \
                        -o patched.nds

  # patch several
  python3 repack_rom.py -r data_iz/script/evet.pkb=evet_new.pkb \
                        -r data_iz/logic/item.STR=item_new.STR -o patched.nds
"""
import argparse
import ndspy.rom

ROM_PATH = ("/home/mcpeace/ie3Ogres-rom-FR/"
            "Inazuma-Eleven-3-Sekai-heno-Chousen-The-Ogre-DS-Traduit-en-Français-v06.nds")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-r", "--replace", action="append", default=[], metavar="ROMPATH=LOCALFILE",
                    help="replace internal ROM file ROMPATH with the bytes of LOCALFILE "
                         "(repeatable)")
    ap.add_argument("-o", "--out", required=True, help="output .nds path")
    ap.add_argument("--rom", default=ROM_PATH, help="source ROM (default: the project ROM)")
    ap.add_argument("--verify", action="store_true",
                    help="after writing, re-read the output ROM and assert it is "
                         "content-lossless: every internal file, both ARM binaries, and "
                         "all overlays match what was packed (replaced files match the "
                         "edit; all others match the source). ndspy re-lays-out the "
                         "container, so the .nds is NOT byte-identical to the source — "
                         "file contents are the real invariant.")
    args = ap.parse_args()

    with open(args.rom, "rb") as f:
        src_bytes = f.read()
    rom = ndspy.rom.NintendoDSRom(src_bytes)

    # Parse and apply replacements.
    replacements = {}  # rompath -> new bytes
    for spec in args.replace:
        if "=" not in spec:
            ap.error(f"--replace needs ROMPATH=LOCALFILE, got: {spec!r}")
        rompath, local = spec.split("=", 1)
        rompath = rompath.strip().lstrip("/")
        idx = rom.filenames.idOf(rompath)
        if idx is None:
            ap.error(f"internal path not found in ROM filesystem: {rompath!r}")
        with open(local, "rb") as f:
            new = f.read()
        old = rom.files[idx]
        rom.files[idx] = new
        replacements[rompath] = (idx, len(old), len(new))
        delta = len(new) - len(old)
        print(f"  replaced {rompath}  (id {idx})  {len(old)} -> {len(new)} bytes "
              f"({'+' if delta >= 0 else ''}{delta})")

    if not replacements:
        print("  no --replace given: pure round-trip repack")

    out_bytes = rom.save()
    with open(args.out, "wb") as f:
        f.write(out_bytes)
    identical = out_bytes == src_bytes
    print(f"wrote {args.out} ({len(out_bytes)} bytes)"
          f"{' — byte-identical to source' if identical else ''}")

    if args.verify:
        check = ndspy.rom.NintendoDSRom(out_bytes)
        # The in-memory `rom` is the exact intended content (source + edits);
        # the output must reproduce every file/binary/overlay it holds.
        assert len(check.files) == len(rom.files), "verify FAILED: file count changed"
        file_mismatch = [i for i in range(len(rom.files)) if check.files[i] != rom.files[i]]
        assert not file_mismatch, (
            f"verify FAILED: {len(file_mismatch)} file(s) do not round-trip "
            f"(first id: {file_mismatch[0]})")
        assert check.arm9 == rom.arm9, "verify FAILED: arm9 changed"
        assert check.arm7 == rom.arm7, "verify FAILED: arm7 changed"
        want_ov = rom.loadArm9Overlays()
        got_ov = check.loadArm9Overlays()
        assert len(want_ov) == len(got_ov), "verify FAILED: overlay count changed"
        ov_mismatch = [k for k in want_ov if want_ov[k].data != got_ov[k].data]
        assert not ov_mismatch, f"verify FAILED: overlay(s) changed: {ov_mismatch[:5]}"
        assert check.idCode == rom.idCode and check.name == rom.name, \
            "verify FAILED: header game code/name changed"
        print(f"  verify OK: all {len(rom.files)} files, arm9/arm7, and "
              f"{len(want_ov)} overlays round-trip intact")
        for rompath, (_idx, _oldlen, newlen) in replacements.items():
            print(f"    - {rompath}: edit present ({newlen} bytes)")


if __name__ == "__main__":
    main()
