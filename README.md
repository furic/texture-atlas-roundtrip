# texture-atlas-roundtrip

A Claude Code skill for splitting packed UV texture atlases into per-island PNGs, editing each piece independently in any AI image tool (ChatGPT, DALL-E, Stable Diffusion, Photopea, etc.), and compositing the edits back at exact pixel coordinates without UV bleed.

Built for retexturing 3D character clothing/accessories piece-by-piece while keeping the rest of the atlas untouched.

## Why

Texture atlases pack UV islands tightly to save memory. Rectangular crops of an atlas always pull in slivers of neighbor islands. This skill uses **connected-component labeling** to extract each island cleanly, with neighbors masked to pure black — perfect for AI image tools that need a solid background.

The composite step uses a `(AI silhouette ∩ original silhouette)` mask, so:

- Neighbor UV islands sharing the bbox are **not** overwritten by AI's black
- AI content drawn beyond the original silhouette is clipped (no UV bleed)

## Install

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/furic/texture-atlas-roundtrip ~/.claude/skills/texture-atlas-roundtrip
```

Requires Python 3 with `numpy`, `Pillow`, and `scipy`:

```bash
pip install numpy Pillow scipy
```

## Quickstart

```bash
SKILL=~/.claude/skills/texture-atlas-roundtrip

# 1. Split a packed atlas into per-island PNGs + manifest.json
python3 $SKILL/split.py atlas.png ./pieces/

# 2. Edit ./pieces/manifest.json: rename auto-numbered pieces
#    (island_0 → shirt_front, island_1 → hat, etc.)

# 3. Send a piece (e.g. shirt_front.png) to ChatGPT / DALL-E / SD with a prompt
#    asking to keep dimensions 1024×1024 and a pure black background.
#    Save the result back as shirt_front_edited.png.

# 4. Composite the edited piece back into the atlas
python3 $SKILL/composite.py atlas.png shirt_front shirt_front_edited.png ./pieces/manifest.json
```

### Y-Flipped UV Islands

Many UV unwraps are stored vertically flipped (e.g. shirt collar at the BOTTOM of the texture, hem at the TOP). When AI draws on such a piece, its details land upside-down on the 3D mesh.

Two-flip workaround:

```bash
# Pre-flip the piece so AI sees natural orientation
python3 $SKILL/flip_piece.py shirt_front.png

# Send shirt_front_flipped.png to AI, save result back

# In manifest.json, set "flip_y": true on the piece's entry
# composite.py auto-flips the AI result during paste-back
python3 $SKILL/composite.py atlas.png shirt_front result.png ./pieces/manifest.json
# (or pass --flip-y to override)
```

See [SKILL.md](SKILL.md) for the full reference: technique, common mistakes, paste-back masking logic, and Y-flip handling.

## Optional: Slash Command Shortcuts

If you want `/split-texture` and `/merge-texture` shortcuts in Claude Code, copy the example skill files:

```bash
mkdir -p ~/.claude/skills/split-texture ~/.claude/skills/merge-texture
cp examples/split-texture-SKILL.md ~/.claude/skills/split-texture/SKILL.md
cp examples/merge-texture-SKILL.md ~/.claude/skills/merge-texture/SKILL.md
```

Then in Claude Code:

```
/split-texture @atlas.png ./pieces/
/merge-texture @atlas.png shirt_front @edited.png @manifest.json
```

## What's Included

| File | Purpose |
|------|---------|
| `SKILL.md` | Main reference — when to use, technique, common mistakes |
| `split.py` | Split a packed atlas into per-island PNGs + manifest |
| `composite.py` | Paste an edited piece back into the atlas with intersection mask |
| `flip_piece.py` | Vertically flip a piece PNG (for Y-flipped UVs) |
| `examples/` | Optional slash command skill files |

## License

[MIT](LICENSE)
