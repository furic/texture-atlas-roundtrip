---
name: split-texture
description: Shortcut for texture-atlas-roundtrip split. Use when the user runs /split-texture, asks to split a UV texture atlas into per-island pieces, or wants to extract individual clothing/accessory pieces from a packed texture for AI image-tool editing. Invoke with /split-texture <source.png> [<out_dir>].
---

# Split Texture

Shortcut that runs the `split.py` script from the `texture-atlas-roundtrip` skill to extract each UV island from a packed texture atlas as a standalone 1024×1024 PNG, with neighbors masked to pure black so they can be sent to AI image tools without bleed.

## Usage

```bash
python3 ~/.claude/skills/texture-atlas-roundtrip/split.py <source.png> <out_dir>
```

Default `<out_dir>` if the user doesn't specify: `/tmp/texture_pieces/`.

The `@` prefix in user args (e.g. `/split-texture @atlas.png`) is just a path reference — strip it and use the resolved path.

## Steps

1. Resolve the source PNG path from user args.
2. Pick an output directory (use user's value if given, else `/tmp/texture_pieces/`). Prefer **outside** the project's `Assets/` folder if the source is in a Unity project, so Unity doesn't auto-import each piece as a texture asset.
3. Run the split script via Bash.
4. List the extracted pieces and direct the user to:
   - Edit `<out_dir>/manifest.json` to rename islands semantically (e.g. `island_2` → `shirt_front`).
   - For Y-flipped UVs (chibi/SD characters with collar at the bottom of the texture), pre-flip the piece before sending to AI — see below.
   - Send a piece (e.g. `shirt_front.png`) to ChatGPT / DALL-E / Stable Diffusion with their style prompt.
   - Use `/merge-texture` to composite the AI result back.

## Pre-Flipping Y-Flipped Pieces

If the user knows (or discovers) that a piece's UV is Y-flipped, pre-flip it before sending to AI so the AI works in natural orientation:

```bash
python3 ~/.claude/skills/texture-atlas-roundtrip/flip_piece.py <piece>.png
# -> writes <piece>_flipped.png alongside
```

Send `<piece>_flipped.png` to AI. After AI returns, `composite.py` (and `/merge-texture`) re-flip during paste — set `"flip_y": true` on that piece's manifest entry to make it automatic, or pass `--flip-y` per-invocation.

## Reference

Full technique, paste-back logic, Y-flip handling, and common mistakes: see the `texture-atlas-roundtrip` skill.
