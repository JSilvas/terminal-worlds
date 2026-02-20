#!/bin/zsh

# --- TERMINAL WORLDS ENGINE ---
# Procedural Terminal Backgrounds
#
# Each terminal session gets a unique background from a pre-generated pool.
# One-for-one replenishment: every image claimed spawns a parallel generator,
# so the pool recovers in one generation cycle (~5s) regardless of burst size.

PROJECT_DIR="/Users/jaysilvas/dev/terminal-worlds"
CACHE_DIR="$HOME/.cache/terminal_worlds"
POOL_DIR="$CACHE_DIR/pool"
SESSION_DIR="$CACHE_DIR/sessions"
POOL_TARGET=10

mkdir -p "$POOL_DIR" "$SESSION_DIR"

# --- CORE FUNCTIONS ---

function apply_bg() {
    local bg_path="$1"
    if [[ -z "$ITERM_SESSION_ID" ]]; then return 1; fi

    # AppleScript is the reliable method — works from any context
    osascript -e "tell application \"iTerm2\" to tell current session of current window to set background image to \"$bg_path\"" 2>/dev/null
}

function generate_bg() {
    local output="$1"
    local biome="$2"
    (
        cd "$PROJECT_DIR"
        if [[ -n "$biome" ]]; then
            uv run generate_landscape.py "$output" "$biome"
        else
            uv run generate_landscape.py "$output"
        fi
    ) > /dev/null 2>&1
}

function claim_from_pool() {
    local target="$1"
    # Try each file — mv is atomic, so only one process wins per file
    for img in "$POOL_DIR"/*.png(N); do
        if mv "$img" "$target" 2>/dev/null; then
            return 0
        fi
    done
    return 1
}

# Generate a single image into the pool (used as a parallel unit of work)
function generate_one_for_pool() {
    local tmpfile="$CACHE_DIR/.generating_${$}_${RANDOM}.png"
    generate_bg "$tmpfile"
    if [[ -f "$tmpfile" ]]; then
        mv "$tmpfile" "$POOL_DIR/$(date +%s)_${RANDOM}.png"
    fi
}

# Spawn one background generator to replace a claimed image
function replace_one_async() {
    (generate_one_for_pool &) > /dev/null 2>&1
}

# Fill pool to target — re-checks count before each generation to avoid
# over-producing when multiple warm-up processes run concurrently
function warm_pool() {
    while true; do
        local files=("$POOL_DIR"/*.png(N))
        if (( ${#files} >= POOL_TARGET )); then break; fi
        generate_one_for_pool
    done
}

function warm_pool_async() {
    (warm_pool &) > /dev/null 2>&1
}

# --- MAIN LOGIC ---

if [[ -z "$ITERM_SESSION_ID" ]]; then
    return 0 2>/dev/null || exit 0
fi

SESSION_ID="${ITERM_SESSION_ID//:/_}"
SESSION_BG="$SESSION_DIR/${SESSION_ID}.png"

# 1. Explicit biome request (e.g. `world biome forest`)
if [[ -n "$1" ]]; then
    generate_bg "$SESSION_BG" "$1"
    apply_bg "$SESSION_BG"
    replace_one_async
    return 0 2>/dev/null || exit 0
fi

# 2. Standard flow: claim from pool (instant) or generate on the spot
if claim_from_pool "$SESSION_BG"; then
    apply_bg "$SESSION_BG"
    # One-for-one: replace exactly what we took
    replace_one_async
else
    # Pool empty — generate synchronously for this session
    generate_bg "$SESSION_BG"
    apply_bg "$SESSION_BG"
    # Cold start — warm the entire pool in the background
    warm_pool_async
fi
