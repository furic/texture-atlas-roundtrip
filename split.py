"""Split a packed UV texture atlas into per-island PNGs.

Each output PNG is a clean canvas (default 1024x1024) with one UV island
centered on a pure black background, neighbors masked out using
scipy.ndimage.label (NOT a rectangular crop — that would catch neighbors).

Usage:
    python split.py SRC_TEXTURE.png OUT_DIR [--canvas 1024] [--min-size 20000]

Produces:
    OUT_DIR/island_0.png, island_1.png, ...   (ranked by descending pixel count)
    OUT_DIR/manifest.json                      (bbox, canvas_offset, label_id, scale per piece)

After running, edit manifest.json to give pieces semantic names
(shirt_front, hat, pants, ...) instead of the auto-generated island_N.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def split_atlas(src_path, out_dir, canvas_size=1024, min_pixels=20000):
    img = np.array(Image.open(src_path).convert("RGBA"))
    rgb = img[..., :3]
    # >30 (not >0) tolerates near-black gradients from compression / AI tools
    non_black = rgb.sum(-1) > 30

    labels, n = ndimage.label(non_black)
    sizes = ndimage.sum(non_black, labels, range(1, n + 1))
    slices = ndimage.find_objects(labels)
    ranked = sorted(enumerate(sizes), key=lambda x: -x[1])

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = []
    piece_idx = 0

    for idx, sz in ranked:
        if sz < min_pixels:
            continue
        label_id = idx + 1
        s = slices[idx]
        y0, y1 = s[0].start, s[0].stop
        x0, x1 = s[1].start, s[1].stop
        w, h = x1 - x0, y1 - y0

        # Extract only pixels with this label — black out neighbors
        region = img[y0:y1, x0:x1].copy()
        mask = labels[y0:y1, x0:x1] == label_id
        region[~mask] = [0, 0, 0, 255]

        # Scale down if region exceeds canvas (with 20px margin)
        scale = min(1.0, (canvas_size - 40) / max(w, h))
        if scale < 1.0:
            new_w = int(w * scale)
            new_h = int(h * scale)
            region_pil = Image.fromarray(region, mode="RGBA").resize(
                (new_w, new_h), Image.LANCZOS)
            region = np.array(region_pil)
            cw, ch = new_w, new_h
        else:
            cw, ch = w, h

        canvas = np.zeros((canvas_size, canvas_size, 4), dtype=np.uint8)
        canvas[..., 3] = 255  # opaque
        oy = (canvas_size - ch) // 2
        ox = (canvas_size - cw) // 2
        canvas[oy:oy+ch, ox:ox+cw] = region

        name = f"island_{piece_idx}"
        out_path = out_dir / f"{name}.png"
        Image.fromarray(canvas, mode="RGBA").save(out_path)

        manifest.append({
            "name": name,
            "file": out_path.name,
            "label_id": int(label_id),
            "src_bbox": [int(y0), int(x0), int(y1), int(x1)],
            "src_size": [int(w), int(h)],
            "scale_to_canvas": float(scale),
            "canvas_offset": [int(ox), int(oy)],
            "canvas_size": int(canvas_size),
            "pixel_count": int(sz),
        })
        print(f"  {name:12s} bbox=y[{y0}-{y1}] x[{x0}-{x1}]  {w}x{h} px  -> {out_path.name}")
        piece_idx += 1

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote {len(manifest)} pieces + manifest.json to {out_dir}")
    print(f"Edit manifest.json to rename islands semantically before composite.")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="Source texture PNG (the packed atlas)")
    ap.add_argument("out_dir", help="Output directory for piece PNGs + manifest")
    ap.add_argument("--canvas", type=int, default=1024,
                    help="Output canvas size in px (default 1024)")
    ap.add_argument("--min-size", type=int, default=20000,
                    help="Skip components smaller than N pixels (default 20000)")
    args = ap.parse_args()
    split_atlas(args.src, args.out_dir, args.canvas, args.min_size)


if __name__ == "__main__":
    main()
