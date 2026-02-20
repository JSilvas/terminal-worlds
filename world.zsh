#!/bin/zsh

# --- TERMINAL WORLDS ZSH INTEGRATION ---
# Source this file in your .zshrc:
# source /Users/jaysilvas/dev/terminal-worlds/world.zsh

WORLD_DIR="/Users/jaysilvas/dev/terminal-worlds"
WORLD_SCRIPT="$WORLD_DIR/update_bg.zsh"

function world() {
    case "$1" in
        refresh)
            echo "Generating new landscape..."
            # Force regeneration by bypassing the 'next' cache
            # We do this by calling the script with 'random' (non-existent biome) to force generation
            # Or just call the script which will swap and then regen.
            # Actually, standard update_bg swaps. If we want a FRESH one NOW:
            source "$WORLD_SCRIPT"
            ;;
        biome)
            if [[ -z "$2" ]]; then
                echo "Usage: world biome <forest|desert|corruption|volcanic>"
            else
                echo "Generating $2 landscape..."
                source "$WORLD_SCRIPT" "$2"
            fi
            ;;
        help)
            echo "Terminal Worlds Commands:"
            echo "  refresh      - Swap to next cached background and generate a new one"
            echo "  biome <name> - Generate and set a specific biome"
            echo "  help         - Show this help"
            ;;
        *)
            # Default behavior: swap for current shell session
            # This is what you'd put in .zshrc
            source "$WORLD_SCRIPT"
            ;;
    esac
}

# Auto-apply on new terminal session (Optional: comment out if you prefer manual)
if [[ -n "$ITERM_SESSION_ID" ]]; then
    world
fi
