#!/bin/zsh

# --- TERMINAL WORLDS ENGINE ---
# Procedural Terminal Backgrounds

PROJECT_DIR="/Users/jaysilvas/dev/terminal-worlds"
CACHE_DIR="$HOME/.cache/terminal_worlds"
GENERATOR_SCRIPT="$PROJECT_DIR/generate_landscape.py"

CURRENT_BG="$CACHE_DIR/current.png"
NEXT_BG="$CACHE_DIR/next.png"

# Ensure cache directory exists
mkdir -p "$CACHE_DIR"

function apply_bg() {
    local bg_path="$1"
    # iTerm2 Background Image Escape Code
    if [[ -n "$ITERM_SESSION_ID" ]]; then
        printf "\033]1337;SetBackgroundImageFile=%s\007" "$bg_path"
    fi
}

function generate_bg() {
    local output="$1"
    local biome="$2"
    cd "$PROJECT_DIR"
    if [[ -n "$biome" ]]; then
        # Temporary seed shift or script modification for biome would be needed here
        # For now, we'll just pass it as an arg (the script needs to handle it)
        uv run generate_landscape.py "$output" "$biome" > /dev/null 2>&1
    else
        uv run generate_landscape.py "$output" > /dev/null 2>&1
    fi
}

function generate_next_bg_async() {
    # Run in background, properly detached
    # Use nohup to ensure process survives shell exit
    nohup bash -c "cd '$PROJECT_DIR' && uv run generate_landscape.py '$NEXT_BG' > /dev/null 2>&1" > /dev/null 2>&1 &
}

# --- MAIN LOGIC ---

# 1. Handle command line biome request
if [[ -n "$1" ]]; then
    generate_bg "$CURRENT_BG" "$1"
    apply_bg "$CURRENT_BG"
    exit 0
fi

# 2. Standard flow: swap cached "next" image for instant results
if [[ -f "$NEXT_BG" ]]; then
    mv "$NEXT_BG" "$CURRENT_BG"
    apply_bg "$CURRENT_BG"
    generate_next_bg_async
else
    # Cache miss
    if [[ ! -f "$CURRENT_BG" ]]; then
        generate_bg "$CURRENT_BG"
    fi
    apply_bg "$CURRENT_BG"
    generate_next_bg_async
fi
