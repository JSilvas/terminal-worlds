#!/bin/zsh

# Configuration
PROJECT_DIR="/Users/jaysilvas/.gemini/antigravity/playground/velvet-celestial"
CACHE_DIR="$HOME/.cache/velvet_celestial"
PYTHON_EXEC="$PROJECT_DIR/.venv/bin/python3"
GENERATOR_SCRIPT="$PROJECT_DIR/generate_landscape.py"

CURRENT_BG="$CACHE_DIR/current.png"
NEXT_BG="$CACHE_DIR/next.png"

# Ensure cache directory exists
mkdir -p "$CACHE_DIR"

function apply_bg() {
    local bg_path="$1"
    # iTerm2 proprietary escape code for background image
    # We use printf to avoid issues with echo
    # Format: \033]1337;SetBackgroundImageFile=/path/to/img\007
    printf "\033]1337;SetBackgroundImageFile=%s\007" "$bg_path"
}

function generate_next_bg() {
    # Run in background, detached
    "$PYTHON_EXEC" "$GENERATOR_SCRIPT" "$NEXT_BG" &!
}

# Main Logic
if [[ -f "$NEXT_BG" ]]; then
    # Instant swap
    mv "$NEXT_BG" "$CURRENT_BG"
    apply_bg "$CURRENT_BG"
    
    # Trigger next generation
    generate_next_bg
else
    # First run or cache missing
    if [[ ! -f "$CURRENT_BG" ]]; then
        # Must block to generate at least one
        echo "Generating initial landscape..."
        "$PYTHON_EXEC" "$GENERATOR_SCRIPT" "$CURRENT_BG"
    fi
    
    # Check again (in case we just generated it, or if it was already there)
    if [[ -f "$CURRENT_BG" ]]; then
       apply_bg "$CURRENT_BG"
    fi

    # Trigger next generation so next tab is fast
    generate_next_bg
fi
