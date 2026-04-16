# Terminal Worlds

Procedural pixel-art landscapes as iTerm2 terminal backgrounds.

![Terminal Worlds](terminal-worlds-full.gif)

Each new terminal session gets a unique generated image — a different biome, sky, terrain, structures, and lighting — applied automatically via the iTerm2 AppleScript API.

> **Prototype status.** Works end-to-end on macOS/iTerm2. Paths in `update_bg.zsh` and `world.zsh` are currently hardcoded to the dev directory.

---

## Biomes

| Biome | Sky | Terrain | Liquid |
|-------|-----|---------|--------|
| `forest` | Blue day | Green hills, trees | Water |
| `desert` | Sunset orange | Sandy dunes, cacti | — |
| `corruption` | Dark night | Purple terrain, fungi | Toxic |
| `volcanic` | Dark red | Obsidian, ash | Lava |

---

## Install

```zsh
zsh install.zsh
```

Then add to `~/.zshrc`:

```zsh
source ~/.terminal-worlds/world.zsh
```

Restart or `source ~/.zshrc`. The pool will warm on first session.

**Requirements:** iTerm2, `uv`, Python 3.13+, Pillow (managed via `uv`).

**Recommended:** Go into Settings/Profile/Window/ and change background image scaling to "Scale to Fit".

---

## Usage

```zsh
world            # random background for this session
world forest     # specific biome
world refresh    # swap to next pre-generated background
world help       # show all commands
```

---

## Architecture

```
world.zsh             # user-facing ZSH command
  └── update_bg.zsh   # pool manager: claim → apply → replenish async
        └── generate_landscape.py  # core renderer (1310 lines, Pillow)
```

The pool (`~/.cache/terminal_worlds/pool/`) keeps 10 pre-rendered images so
each new terminal session gets an instant background swap. One image is
replenished asynchronously after each claim.

For a detailed breakdown of rendering stages, biome palettes, and code
conventions see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Contributing

Create issues using the templates in `.github/ISSUE_TEMPLATE/`. Label them
`todo` when they are ready for an agent to pick up. See [WORKFLOW.md](WORKFLOW.md)
for the full agent collaboration protocol, and [CLAUDE.md](CLAUDE.md) for
architecture details and agent guidelines.

```bash
# Run the generator directly
uv run generate_landscape.py /tmp/test.png forest

# Run tests
uv run pytest tests/ -v
```
