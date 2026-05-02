"""Vertically flip a UV island piece PNG.

Use this to pre-flip a piece BEFORE sending to AI when the texture atlas is
unwrapped Y-flipped (e.g. shirt collar at the BOTTOM of the texture). This
lets the AI see the piece in natural orientation and draw details correctly
oriented. After AI returns its result, run composite.py with --flip-y (or
set flip_y: true in the manifest) to flip back during paste.

Usage:
    python flip_piece.py SRC.png [DST.png]

If DST is omitted, defaults to SRC with "_flipped" inserted before extension:
    shirt_front.png -> shirt_front_flipped.png
"""
import argparse
from pathlib import Path
from PIL import Image


def flip(src_path, dst_path=None):
    src = Path(src_path)
    if dst_path:
        dst = Path(dst_path)
    else:
        dst = src.with_name(f"{src.stem}_flipped{src.suffix}")
    img = Image.open(src).transpose(Image.FLIP_TOP_BOTTOM)
    img.save(dst)
    print(f"Flipped: {src} -> {dst}")
    return dst


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="Source piece PNG")
    ap.add_argument("dst", nargs="?", default=None,
                    help="Destination path (default: SRC with _flipped suffix)")
    args = ap.parse_args()
    flip(args.src, args.dst)


if __name__ == "__main__":
    main()
