# terminal-worlds

Procedural pixel-art landscapes as iTerm2 terminal backgrounds.

![Terminal Worlds](terminal-worlds-full.gif)

Each new terminal session gets a unique generated image — a different biome, sky, terrain, structures, and lighting — applied automatically via the iTerm2 AppleScript API.

> **Prototype status.** Works end-to-end on macOS/iTerm2. Paths in `update_bg.zsh` and `world.zsh` are currently hardcoded to the dev directory.

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
world              # Swap to next cached background (runs automatically on new session)
world refresh      # Same as above
world biome <name> # Generate and apply a specific biome
world help         # Show commands
```

**Biomes:** `forest`, `desert`, `corruption`, `volcanic`

---

## Development & Architecture

This repository is optimized for AI agent context. The code is the source of truth rather than a harness of redundant documentation.

For a high-level overview of the implementation, components, and current prototype state, see [ARCHITECTURE.md](ARCHITECTURE.md). For all implementation details, please read the code directly.
