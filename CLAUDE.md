# CLAUDE.md — Agent Guide for Terminal Worlds

This file is the primary instruction set for Claude Code background agents working
on this repository. Read it in full before picking up any issue.

---

## Project Overview

**Terminal Worlds** is a procedural landscape generator that creates pixel-art
backgrounds for iTerm2 terminal sessions. It uses Perlin-like noise, fractal
Brownian Motion, cellular automata, and volumetric lighting techniques to produce
unique 1920×1080 PNG images across four biomes.

### User-facing experience

```
world           # apply a random background to the current iTerm2 session
world forest    # apply a specific biome
world refresh   # cycle to the next pre-generated background
```

A pool-based cache (`~/.cache/terminal_worlds/pool/`) keeps 10 pre-rendered images
ready so users get instant swaps on new sessions. One image is replenished
asynchronously each time one is claimed.

---

## Repository Map

```
terminal-worlds/
├── CLAUDE.md               # This file — agent instructions
├── WORKFLOW.md             # Symphony-style orchestration spec
├── README.md               # User-facing documentation
├── main.py                 # CLI entry point
├── generate_landscape.py   # Core 1310-line generator (the heart of the project)
├── install.zsh             # One-shot installer
├── update_bg.zsh           # Pool manager + iTerm2 background applier
├── world.zsh               # User-facing ZSH command
├── pyproject.toml          # uv project config
├── uv.lock                 # Locked dependencies
├── tests/
│   ├── conftest.py         # pytest fixtures
│   └── test_landscape.py   # Core test suite
└── .github/
    ├── ISSUE_TEMPLATE/     # Structured issue templates
    └── workflows/
        └── ci.yml          # GitHub Actions CI
```

---

## Architecture: generate_landscape.py

The generator is a single-file pipeline with these rendering stages (in order):

| Stage | Lines | Description |
|-------|-------|-------------|
| Sky gradient | 777–785 | Lerp from top to bottom palette color |
| Starfield | 787–793 | Conditional density based on sky brightness |
| Celestial body | 795–815 | Sun/moon with radial glow, 75% spawn rate |
| Clouds | 817–852 | 2×2 block grid, noise-driven, edge-shaded |
| Far mountains | 854–862 | Rigid noise + heavy atmospheric haze |
| Mid mountains | 864–904 | Domain-warped to break striping, rim lighting |
| Foreground terrain | 906–1002 | Height map, water/lava, ground cover, vines |
| Deep strata | 1004–1025 | Layered rock colors + macro ore veins |
| Structures | 1037–1068 | Chunked monoliths/ruins/arches with collision masks |
| Lava glow | 1069–1123 | Volcanic post-pass, warm corona effect |
| Trees & vines | 1125–1160 | Collision-aware tree placement |
| Bloom + god rays | 1162–1299 | Hot-pixel bloom, radial volumetric shafts |

**Key classes:**

- `SmoothNoise` — Perlin-like 2D noise with fBm support and rigid mode for ridged terrain
- `Palette` — Complete biome color scheme (sky, ground, water, strata, rune colors, light direction)
- `generate_landscape(output_path, biome_name)` — Main orchestrator; `biome_name` is one of `forest | desert | corruption | volcanic`

**Collision mask** (`cols` dict): a 2D dict keyed `(x, y)` → `{0: sky, 1: mid, 2: foreground}`.
Higher layers occlude lower layers. All structure/tree functions receive and update this mask.

---

## Biomes

| Name | Sky | Ground | Water | Structures |
|------|-----|--------|-------|------------|
| `forest` | Blue | Green | Cyan | Stone, trees, ferns |
| `desert` | Orange sunset | Sandy | None | Cacti, sand dunes |
| `corruption` | Dark night | Purple | Toxic green | Biolume fungi, moon |
| `volcanic` | Dark red | Charcoal | Lava | Ash clouds, lava glow |

---

## Development Setup

```bash
# Install dependencies (uv required)
uv sync

# Run the generator manually
uv run generate_landscape.py --biome forest --output /tmp/test.png

# Run tests
uv run pytest tests/ -v

# Run a single test
uv run pytest tests/test_landscape.py::test_noise_range -v
```

> If `uv` is not installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## Code Conventions

- **Python 3.13+**; use only stdlib + Pillow unless the issue explicitly calls for a new dependency
- **No type annotations** on existing functions unless you are refactoring that specific function
- **No docstrings** on existing functions unless the issue asks for documentation
- Match the existing style: procedural with module-level functions, no classes beyond the two existing ones
- Image coordinates: `(0,0)` is top-left; `x` is column, `y` is row
- All noise functions expect normalized float inputs; do not pass raw pixel coordinates without dividing by width/height or a frequency scale
- Color tuples are always `(R, G, B)` integers 0–255; no alpha channel in the main canvas
- Use `random.seed(seed)` and `SmoothNoise(seed)` so outputs are reproducible when a seed is passed

---

## Testing Strategy

Tests live in `tests/`. Run with `uv run pytest`.

**What to test:**
- `SmoothNoise`: Output range [0, 1], determinism with same seed, variation with different seeds
- `Palette`: All four biomes instantiate without error, required attributes exist
- `generate_landscape`: Produces a valid PNG at 1920×1080, does not crash for any biome
- New features: Any new function must have at least one test covering the happy path

**What not to test:**
- Visual/aesthetic correctness — use the generated PNG files for manual review
- Internal rendering order — treat the pipeline as a black box at the test level
- Shell scripts (install.zsh, update_bg.zsh) — not in scope for pytest

---

## Branch & PR Workflow

1. **Branch name**: `claude/<short-description>-<session-id>` (the session-id suffix is auto-set by the harness; do not invent it)
2. **One branch per issue** — never put two issues' changes on the same branch
3. **Commit messages**: Imperative mood, ≤72 chars, e.g. `feat: add snow biome with blizzard effects`
4. **PR title**: Match the issue title closely
5. **PR body**: Use the template in `.github/PULL_REQUEST_TEMPLATE.md` if present; otherwise include: what changed, how to verify, and the closing issue reference (`Closes #N`)
6. **CI must be green** before requesting review — do not open a PR with failing tests
7. **Never push to `main` or `master`** directly

---

## How to Pick Up an Issue

1. Find an open issue labeled `todo` in GitHub Issues
2. Read the issue fully — check for acceptance criteria and any linked discussion
3. Add the label `in-progress` and assign yourself (use `gh issue edit N --add-label in-progress`)
4. Create your branch: `git checkout -b claude/<slug>-<session-id>`
5. Implement the feature/fix. Run `uv run pytest` to validate.
6. Push and open a PR: `gh pr create ...`
7. Add label `in-review` to the issue and remove `in-progress`
8. When the PR merges, the issue should be auto-closed via `Closes #N` in the PR body

---

## Blockers & Communication

- If you are blocked (missing information, ambiguous spec, test infrastructure broken), leave a comment on the issue explaining the blocker and remove the `in-progress` label so another agent or human can pick it up
- Do not silently stall — always leave a trail
- Do not modify `main`, `master`, or another agent's in-progress branch

---

## Background Agent Concurrency

- Multiple background agents may run simultaneously; each works on a separate issue
- Agents share no in-memory state — all coordination happens through git branches and GitHub issue labels
- If two agents open PRs that touch the same file, standard git conflict resolution applies — rebase on `main` before pushing
- Maximum recommended concurrent agents: **3** (to avoid overwhelming CI runners)
