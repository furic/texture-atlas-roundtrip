# Texture Atlas Roundtrip

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-D97757.svg)](https://claude.com/claude-code)
[![GitHub stars](https://img.shields.io/github/stars/furic/texture-atlas-roundtrip?style=flat&logo=github)](https://github.com/furic/texture-atlas-roundtrip/stargazers)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/furic/texture-atlas-roundtrip/pulls)

Texture Atlas Roundtrip is a Claude Code skill for editing one piece of a packed UV texture atlas without disturbing the others — splitting a 3D character's atlas into per-island PNGs, sending each piece to any AI image tool (ChatGPT, DALL-E, Stable Diffusion, Photopea), and compositing edits back at exact pixel coordinates.

## How it works

Texture atlases pack multiple UV islands tightly to save memory. A naive rectangular crop pulls in slivers of the neighboring islands, so anything you send to an AI tool comes back contaminated. Connected-component labeling solves this — it isolates one island's pixels and masks the rest to pure black, giving the AI a clean, solid-background canvas to work on.

When the AI returns its result, the same labels become the paste-back mask. The composite step uses the intersection of the AI's silhouette and the original silhouette: AI black inside the original bbox doesn't overwrite neighbor islands, and AI content drawn beyond the original silhouette gets clipped (no UV bleed).

For UV unwraps that are stored vertically flipped relative to mesh space (a common pattern in chibi/SD characters where the shirt collar lands at the bottom of the texture), pieces can be pre-flipped before sending to AI and the flip is auto-undone during composite — controlled by a `flip_y` field on each piece's manifest entry.

## Installation

Clone into your Claude Code skills directory:

```bash
git clone https://github.com/furic/texture-atlas-roundtrip ~/.claude/skills/texture-atlas-roundtrip
```

Requires Python 3.9+ with `numpy`, `Pillow`, and `scipy`:

```bash
pip install numpy Pillow scipy
```

### Optional: Slash Command Shortcuts

For `/split-texture` and `/merge-texture` shortcuts in Claude Code, copy the example skill files:

```bash
mkdir -p ~/.claude/skills/split-texture ~/.claude/skills/merge-texture
cp ~/.claude/skills/texture-atlas-roundtrip/examples/split-texture-SKILL.md \
   ~/.claude/skills/split-texture/SKILL.md
cp ~/.claude/skills/texture-atlas-roundtrip/examples/merge-texture-SKILL.md \
   ~/.claude/skills/merge-texture/SKILL.md
```

## Quickstart

```bash
SKILL=~/.claude/skills/texture-atlas-roundtrip

# 1. Split a packed atlas into per-island PNGs + manifest.json
python3 $SKILL/split.py atlas.png ./pieces/

# 2. Edit ./pieces/manifest.json: rename auto-numbered pieces semantically
#    (island_0 → shirt_front, island_1 → hat, etc.)

# 3. Send a piece (e.g. shirt_front.png) to any AI image tool with a prompt
#    asking to keep dimensions 1024×1024 and a pure black background.
#    Save the result back as shirt_front_edited.png.

# 4. Composite the edited piece back into the atlas
python3 $SKILL/composite.py atlas.png shirt_front shirt_front_edited.png ./pieces/manifest.json
```

### Y-Flipped UV Islands

If pockets, logos, or other asymmetric details land upside-down on the 3D model after the first composite, the UV is Y-flipped. Pre-flip the piece so the AI works in natural orientation:

```bash
python3 $SKILL/flip_piece.py shirt_front.png
# → writes shirt_front_flipped.png
```

Then add `"flip_y": true` to that piece's `manifest.json` entry. Composite auto-flips on paste-back. No re-prompting needed once the AI input was sent in natural orientation.

## What's Inside

| File | Purpose |
|------|---------|
| `SKILL.md` | Main reference — when to use, technique, paste-back logic, common mistakes |
| `split.py` | Split a packed atlas into per-island PNGs + manifest |
| `composite.py` | Paste an edited piece back with intersection mask (`--flip-y` supported) |
| `flip_piece.py` | Vertically flip a piece PNG, for Y-flipped UVs |
| `examples/` | Optional `/split-texture` and `/merge-texture` slash command skills |

See [`SKILL.md`](SKILL.md) for the full reference, including common mistakes and the paste-back masking logic.

## Contributing

Issues and PRs welcome. For new technique improvements, please include a before/after example showing the failure mode the change addresses.

## License

MIT License — see [LICENSE](LICENSE) for details.
