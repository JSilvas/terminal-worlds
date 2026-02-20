#!/bin/zsh

# --- TERMINAL WORLDS INSTALLER ---
# Deploys the engine to ~/.terminal-worlds

INSTALL_DIR="$HOME/.terminal-worlds"
SOURCE_DIR=$(pwd)

echo "Installing Terminal Worlds to $INSTALL_DIR..."

# 1. Create Directory
mkdir -p "$INSTALL_DIR"

# 2. Copy Core Files
cp "$SOURCE_DIR/generate_landscape.py" "$INSTALL_DIR/"
cp "$SOURCE_DIR/pyproject.toml" "$INSTALL_DIR/"
cp "$SOURCE_DIR/uv.lock" "$INSTALL_DIR/"
cp "$SOURCE_DIR/update_bg.zsh" "$INSTALL_DIR/"
# 3. Copy Integration Script
cp "$SOURCE_DIR/world.zsh" "$INSTALL_DIR/"

# 4. Update Paths
# Update PROJECT_DIR in update_bg.zsh
# We use | as delimiter for sed to avoid issues with slashes in paths
sed -i '' "s|PROJECT_DIR=.*|PROJECT_DIR=\"$INSTALL_DIR\"|" "$INSTALL_DIR/update_bg.zsh"

# Update WORLD_DIR in world.zsh
sed -i '' "s|WORLD_DIR=.*|WORLD_DIR=\"$INSTALL_DIR\"|" "$INSTALL_DIR/world.zsh"

# 5. Permissions
chmod +x "$INSTALL_DIR/update_bg.zsh"
chmod +x "$INSTALL_DIR/world.zsh"

echo "Installation Complete!"
echo ""
echo "To enable the 'world' command, add this line to your ~/.zshrc:"
echo "source $INSTALL_DIR/world.zsh"
echo ""
echo "Then restart your terminal or run 'source ~/.zshrc'"
