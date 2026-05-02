"""Composite an edited UV island PNG back into the source texture atlas.

Uses (AI silhouette ∩ original silhouette) as the paste mask so:
  - Neighbor UV islands sharing the bbox are NOT overwritten by AI's black
  - AI content drawn beyond the original silhouette is clipped (no UV bleed)

Usage:
    python composite.py TARGET.png PIECE_NAME EDITED.png MANIFEST.json
                        [--src SRC.png] [--flip-y | --no-flip-y]

TARGET.png    : the texture to update (modified in place; back it up first!)
PIECE_NAME    : name of the piece in MANIFEST.json (e.g. "shirt_front")
EDITED.png    : the AI-edited piece. Any size — auto-cropped to its silhouette
                bbox and resized to the original piece dimensions.
MANIFEST.json : produced by split.py; provides src_bbox + label_id.
--src SRC.png : (optional) source texture for the original silhouette mask.
                Defaults to TARGET.
--flip-y      : vertically flip the AI image before compositing. Use when the
                UV is unwrapped Y-flipped (e.g. shirt collar at the BOTTOM of
                the texture). Overrides any flip_y setting in the manifest.
--no-flip-y   : force NO flip even if manifest entry has flip_y: true.

Manifest persistence: if a piece's manifest entry has "flip_y": true,
flipping is auto-applied without needing the CLI flag. Set this once per
atlas after discovering which pieces are Y-flipped.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def composite_piece(target_path, piece_name, edited_path, manifest_path,
                    src_path=None, flip_y=None):
    manifest = json.loads(Path(manifest_path).read_text())
    entry = next((m for m in manifest if m["name"] == piece_name), None)
    if entry is None:
        print(f"ERROR: piece '{piece_name}' not found in manifest", file=sys.stderr)
        print(f"Available: {[m['name'] for m in manifest]}", file=sys.stderr)
        sys.exit(1)

    y0, x0, y1, x1 = entry["src_bbox"]
    label_id = entry["label_id"]
    target_w = x1 - x0
    target_h = y1 - y0

    # Resolve effective flip: CLI overrides manifest; manifest default is False
    effective_flip_y = bool(entry.get("flip_y", False)) if flip_y is None else bool(flip_y)

    # Load AI-edited piece, optionally flip Y, then find its content bbox
    edited_pil = Image.open(edited_path).convert("RGBA")
    if effective_flip_y:
        edited_pil = edited_pil.transpose(Image.FLIP_TOP_BOTTOM)
    edited = np.array(edited_pil)
    edited_rgb = edited[..., :3]
    ai_nb = edited_rgb.sum(-1) > 30   # threshold tolerates near-black gradients
    if ai_nb.sum() == 0:
        print("ERROR: edited image is entirely black", file=sys.stderr)
        sys.exit(1)
    ys, xs = np.where(ai_nb)
    ay0, ay1 = ys.min(), ys.max() + 1
    ax0, ax1 = xs.min(), xs.max() + 1

    # Crop AI to its silhouette bbox, resize to original piece size
    edited_crop = Image.fromarray(edited_rgb[ay0:ay1, ax0:ax1], mode="RGB")
    edited_resized = np.array(
        edited_crop.resize((target_w, target_h), Image.LANCZOS))

    # Compute masks
    ai_resized_nb = edited_resized.sum(-1) > 30

    src_path = src_path or target_path
    src_img = np.array(Image.open(src_path).convert("RGB"))
    src_nb = src_img.sum(-1) > 30
    src_labels, _ = ndimage.label(src_nb)
    orig_mask = src_labels[y0:y1, x0:x1] == label_id

    # The critical mask: intersection of AI silhouette and original silhouette
    combined = ai_resized_nb & orig_mask
    combined_eroded = ndimage.binary_erosion(combined, iterations=1)
    mask_smooth = ndimage.gaussian_filter(
        combined_eroded.astype(np.float32), sigma=0.7)
    mask3 = mask_smooth[..., None]

    # Composite into target
    target = np.array(Image.open(target_path).convert("RGBA"))
    target_region = target[y0:y1, x0:x1, :3].astype(np.float32)
    blended = edited_resized.astype(np.float32) * mask3 + target_region * (1.0 - mask3)
    target[y0:y1, x0:x1, :3] = np.clip(blended, 0, 255).astype(np.uint8)

    Image.fromarray(target, mode="RGBA").save(target_path)
    flip_note = " (Y-flipped)" if effective_flip_y else ""
    print(f"Composited '{piece_name}' into {target_path}{flip_note}")
    print(f"  AI source bbox y[{ay0}-{ay1}] x[{ax0}-{ax1}] resized to {target_w}x{target_h}")
    print(f"  Pasted at target bbox y[{y0}-{y1}] x[{x0}-{x1}]")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("piece_name")
    ap.add_argument("edited")
    ap.add_argument("manifest")
    ap.add_argument("--src", default=None,
                    help="Source texture for original silhouette mask (defaults to target)")
    ap.add_argument("--flip-y", action=argparse.BooleanOptionalAction, default=None,
                    dest="flip_y",
                    help="Flip AI image vertically. Overrides manifest's flip_y. "
                         "Use --no-flip-y to force off.")
    args = ap.parse_args()
    composite_piece(args.target, args.piece_name, args.edited,
                    args.manifest, args.src, args.flip_y)


if __name__ == "__main__":
    main()
