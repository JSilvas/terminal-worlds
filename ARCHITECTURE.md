# Architecture

High-level map of the prototype for agent/developer context. The code is the source of truth — read the files directly for details.

---

## Files

| File | Role |
|------|------|
| `generate_landscape.py` | Core image generator — all terrain, biomes, rendering |
| `update_bg.zsh` | Pool engine — claim, replenish, apply via AppleScript |
| `world.zsh` | ZSH integration — user commands + auto-apply on session start |
| `install.zsh` | Copies files to `~/.terminal-worlds`, patches hardcoded paths |
| `pyproject.toml` | Python project config, Pillow dependency |
| `main.py` | Placeholder — ignore |

---

## Image Generation Pipeline (`generate_landscape.py`)

`generate_landscape.py` is the core image generator handling all terrain, biomes, rendering, structures, and lighting. It upscales a core layout and layers features like sky gradients, starfields, mountains, terrain, flora, and structures via compositing and noise functions.
**See `generate_landscape.py` directly** for the pipeline steps, noise implementations, and structure drawing scripts.
**Adding biomes:** Add a new `Palette` entry to the `BIOMES` list within the generator.

---

## Pool Engine

- **Pool Manager:** `update_bg.zsh`
- **Cache Location:** `~/.cache/terminal_worlds/`

For details on atomic claiming, async replenishment, and iTerm2 bindings, read `update_bg.zsh`.

---

## Known Limitations (Prototype)

- Paths in `update_bg.zsh` and `world.zsh` are hardcoded and patched on install.
- Only iTerm2 on macOS is explicitly supported via AppleScript.
- `main.py` is an unused placeholder.
