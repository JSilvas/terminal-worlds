# Terminal Worlds

Procedural pixel-art landscape generator for iTerm2 terminal backgrounds.
Generates unique 1920×1080 PNG images across four biomes using Perlin-like
noise, cellular automata, and volumetric lighting.

## Biomes

| Biome | Sky | Terrain | Liquid |
|-------|-----|---------|--------|
| `forest` | Blue day | Green hills, trees | Water |
| `desert` | Sunset orange | Sandy dunes, cacti | — |
| `corruption` | Dark night | Purple terrain, fungi | Toxic |
| `volcanic` | Dark red | Obsidian, ash | Lava |

## Installation

```zsh
git clone https://github.com/JSilvas/terminal-worlds
cd terminal-worlds
./install.zsh
# Follow the printed instructions to add world.zsh to .zshrc
```

Requires: macOS, iTerm2, Python 3.13+, [uv](https://github.com/astral-sh/uv)

## Usage

```zsh
world            # random background for this session
world forest     # specific biome
world refresh    # swap to next pre-generated background
world help       # show all commands
```

## Development

See [CLAUDE.md](CLAUDE.md) for architecture details and agent guidelines.
See [WORKFLOW.md](WORKFLOW.md) for the team issue and PR workflow.

```bash
# Run the generator directly
uv run generate_landscape.py /tmp/test.png forest

# Run tests
uv run pytest tests/ -v
```

## Architecture

```
world.zsh             # user-facing ZSH command
  └── update_bg.zsh   # pool manager: claim → apply → replenish async
        └── generate_landscape.py  # core renderer (1310 lines, Pillow)
```

The pool (`~/.cache/terminal_worlds/pool/`) keeps 10 pre-rendered images so
each new terminal session gets an instant background swap. One image is
replenished asynchronously after each claim.

## Contributing

Create issues using the templates in `.github/ISSUE_TEMPLATE/`. Label them
`todo` when they are ready for an agent to pick up. See [WORKFLOW.md](WORKFLOW.md)
for the full agent collaboration protocol.
