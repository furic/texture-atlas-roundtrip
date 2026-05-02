---
name: texture-atlas-roundtrip
description: Use when editing one UV island of a 3D texture atlas without disturbing neighbors, when sending individual pieces of a packed atlas to AI image generation (ChatGPT, DALL-E, Stable Diffusion) and merging results back, or when rectangular crops of a texture atlas pull in slivers of adjacent UV islands.
---

# Texture Atlas Roundtrip

## Overview

Split a packed texture atlas into per-island PNGs (each piece on a clean black canvas, neighbors masked out), edit each piece independently in any image AI, then composite the edits back at exact pixel coordinates. Connected-component labeling does the heavy lifting — rectangular crops of an atlas always pull in adjacent islands; label-based extraction does not.

## When to Use

- Editing one part of a UV-packed texture (shirt, hat, pants, weapon) without touching adjacent islands
- Sending a single atlas piece to ChatGPT / DALL-E / Stable Diffusion / Photopea and merging the result back
- Rectangular crops of the atlas always include slivers of neighbor islands
- Iterating region by region on a 3D character's clothing/accessory textures
- Round-tripping pieces through multiple AI tools without UV bleed

## Core Pattern

**Wrong: rectangular crop**
```python
piece = atlas[y0:y1, x0:x1]   # picks up neighbor islands packed in the same bbox
```

**Right: connected-component label extraction**
```python
labels, n = scipy.ndimage.label(atlas_non_black_mask)
piece = atlas[y0:y1, x0:x1].copy()
piece[labels[y0:y1, x0:x1] != target_label] = 0   # mask other islands black
```

## Quick Reference

| Step | What |
|------|------|
| 1. Detect islands | `scipy.ndimage.label()` on the non-black mask |
| 2. Extract one | Crop bbox AND zero pixels where label ≠ target |
| 3. Center on canvas | 1024×1024 black background, piece centered |
| 4. Save manifest | `{name, src_bbox, canvas_offset, label_id, scale, flip_y?}` per piece |
| 5. (Optional) Pre-flip | If UV is Y-flipped, run `flip_piece.py` so AI sees natural orientation |
| 6. AI edits piece | Send PNG to AI with "pure black background, same dimensions" |
| 7. Composite back | Find AI silhouette → resize to original bbox size → paste with intersection mask (auto-flips if `flip_y` set) |

**Critical paste-back mask:** `(AI_silhouette > 0) & (original_silhouette > 0)`
- Original-only would let AI's black overwrite neighbors that share the bbox
- AI-only would let AI draw outside the original UV silhouette and cause UV bleed
- Intersection covers both directions

## Y-Flipped UV Islands

Many UV unwraps are stored vertically flipped relative to 3D mesh space (e.g. shirt collar at the BOTTOM of the texture, hem at the TOP). When you send such a piece to AI, the AI draws details (pockets, logos) in the canvas-natural-up direction, but those details land upside-down on the 3D model.

**Symptom:** pockets/labels/asymmetric details appear flipped or in the wrong half of the body in 3D preview, even though silhouette and color look correct.

**Two-flip solution** — keep AI working in natural orientation:
1. Pre-flip the piece before sending to AI: `python flip_piece.py shirt_front.png shirt_front_flipped.png`
2. Send the flipped PNG to AI with the standard prompt.
3. After AI returns, composite back with auto-unflip via either:
   - **Persistent (recommended):** add `"flip_y": true` to that piece's manifest entry. Future composites auto-flip.
   - **Per-invocation:** `composite.py ... --flip-y` (overrides manifest).

**Discovery flow:** if the first composite of a piece looks upside-down on the 3D model, set `flip_y: true` in its manifest entry and re-composite. No re-prompt needed for the AI side once AI input was pre-flipped.

## Implementation

Working scripts in this skill directory (Python 3 + numpy + Pillow + scipy):

- `split.py SRC.png OUT_DIR/` — splits atlas into per-island PNGs + `manifest.json`
- `composite.py TARGET.png PIECE_NAME EDITED.png MANIFEST.json [--flip-y|--no-flip-y]` — composites edited piece back; honors `flip_y` in manifest unless overridden by CLI flag
- `flip_piece.py SRC.png [DST.png]` — vertically flips a piece PNG; use to pre-flip AI inputs

All parametrized via CLI args. Copy and adapt — they are minimal and self-contained.

After splitting, edit `manifest.json` to give pieces semantic names (`shirt_front`, `hat`, etc.) instead of `island_0`, `island_1`. Pass these names to `composite.py`. Add `"flip_y": true` to entries whose UV is Y-flipped relative to 3D space.

## Common Mistakes

- **Overwriting the source texture** — always read source, write to a separate file. Keep an untouched original (or a `*_backup.png`). Restoring from backup is annoying mid-iteration.
- **Rectangular crop catches neighbors** — `scipy.ndimage.label` is the only reliable way to isolate one UV island from a packed atlas. There is no "tighter bbox" that fixes this.
- **Using only original silhouette as paste mask** — wherever AI returned black inside the bbox (e.g. it ignored a small adjacent UV island as if it were background), that black overwrites the target. Intersection mask prevents this.
- **Using only AI silhouette as paste mask** — AI sometimes draws beyond the original silhouette, creating UV bleed onto invisible mesh areas. Intersection clips it back.
- **Forgetting the canvas offset / bbox in the manifest** — without it, you cannot restore the piece to its exact original pixel location.
- **AI returns different canvas dimensions** — DALL-E often outputs 1024×1024 or 1792×1024 even when sent 1024×1024. Always find the AI's content bbox in its output and resize to match the original piece dimensions before pasting.
- **Soft-black or gradient backgrounds from AI** — DALL-E sometimes returns near-black gradients instead of pure RGB(0,0,0). Always threshold non-black at `sum > 30` (not `> 0`) to handle this. If AI keeps producing gradients, prompt: "pure RGB(0,0,0) pitch black, no gradient."
- **Skipping the manifest** — when iterating across many pieces, hand-tracking bboxes is error-prone. Always serialize.
- **Ignoring Y-flipped UV islands** — chibi/SD characters often store the shirt UV with collar at the bottom. AI drawing pockets in the "upper canvas" lands them on the wearer's waist (and upside-down) in 3D. See the Y-Flipped UV Islands section above.

## When NOT to Use

- Texture has only one UV island (no atlas) — direct edit is fine
- The change is a global recolor across the whole texture — recolor in-place with HSV ops
- The change is purely procedural (e.g. uniform khaki across all fabric pixels) — algorithmic recolor is faster and deterministic
