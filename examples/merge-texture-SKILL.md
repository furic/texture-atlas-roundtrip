---
name: merge-texture
description: Shortcut for texture-atlas-roundtrip composite. Use when the user runs /merge-texture, asks to merge or composite an AI-edited UV island piece back into a texture atlas, or wants to paste an edited piece (e.g. shirt_front.png from ChatGPT) back at its exact UV position. Invoke with /merge-texture <target.png> <piece_name> <edited.png> [<manifest.json>] [--flip-y | --no-flip-y].
---

# Merge Texture

Shortcut that runs the `composite.py` script from the `texture-atlas-roundtrip` skill to paste an AI-edited UV island PNG back into the source texture atlas at its exact original pixel coordinates, using the AI ∩ original silhouette intersection mask so neighbor islands stay protected.

## Usage

```bash
python3 ~/.claude/skills/texture-atlas-roundtrip/composite.py \
    <target.png> <piece_name> <edited.png> <manifest.json> \
    [--flip-y | --no-flip-y]
```

The `@` prefix in user args is just a path reference — strip it and use the resolved path.

## Args

- `<target.png>` — atlas to update (modified IN PLACE; warn the user to back up first)
- `<piece_name>` — semantic name from the manifest (e.g. `shirt_front`, `hat`)
- `<edited.png>` — AI-edited piece, any size (auto-cropped + resized)
- `<manifest.json>` — produced by `split.py`. If omitted, look in the directory of `<edited.png>` first.
- `--flip-y` / `--no-flip-y` — vertically flip the AI image before compositing. Use when the UV is unwrapped Y-flipped (e.g. shirt collar at the bottom of the texture). Overrides the manifest's `flip_y` field. If neither flag is given, the manifest's `flip_y` is honored (defaults to false).

## Y-Flip Notes

If the target atlas has Y-flipped UVs (common for chibi/SD characters with the shirt collar at the bottom of the texture), the `flip_y` field on each manifest entry handles this automatically:

- Set `"flip_y": true` on a piece's manifest entry once you've confirmed it needs flipping. Future merges of that piece auto-flip — no CLI flag needed.
- Use `--flip-y` for ad-hoc / discovery merges before deciding whether to persist in the manifest.
- Use `--no-flip-y` to force off even when the manifest says true.

If the user pre-flipped the AI input via `flip_piece.py`, they still need `flip_y: true` (or `--flip-y`) on composite — the two flips combine to undo the UV's Y-inversion correctly.

## Steps

1. Resolve all paths from user args.
2. **Warn user about in-place modification** if `<target.png>` doesn't have an obvious backup nearby (e.g. `<target> copy.png` or `<target>.bak`). Offer to copy first.
3. Run the composite script (with `--flip-y` only if user explicitly asked or it's a known-flipped piece without `flip_y` set in manifest).
4. Read the resulting PNG and show the user, OR tell them to preview in their 3D engine.

## Reference

Full technique, paste-back masking logic (`AI silhouette ∩ original silhouette`), Y-flip handling, and common mistakes: see the `texture-atlas-roundtrip` skill.
