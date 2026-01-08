#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}       Moonlight Uninstaller             ${NC}"
echo -e "${BLUE}=========================================${NC}"

echo -e "${GREEN}[1/4] Removing Desktop Shortcut...${NC}"
if [ -f "$HOME/.local/share/applications/Moonlight.desktop" ]; then
    rm "$HOME/.local/share/applications/Moonlight.desktop"
    echo "Removed shortcut."
elif [ -f "$HOME/.local/share/applications/Moonlight.desktop" ]; then
    rm "$HOME/.local/share/applications/Moonlight.desktop"
    echo "Removed shortcut."
else
    echo -e "${YELLOW}No shortcut found (Skipping).${NC}"
fi

echo -e "${GREEN}[2/4] Removing Configuration...${NC}"
if [ -d "$HOME/.config/Moonlight" ]; then
    rm -rf "$HOME/.config/Moonlight"
    echo "Removed ~/.config/Moonlight"
else
    echo -e "${YELLOW}No config found (Skipping).${NC}"
fi

echo -e "${GREEN}[3/4] Removing System Permissions...${NC}"
RULE_FILE="/etc/udev/rules.d/99-Moonlight.rules"

if [ -f "$RULE_FILE" ]; then
    echo -e "${YELLOW}Admin access required to remove system rules.${NC}"
    if sudo rm "$RULE_FILE"; then
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo "Rules removed and system updated."
    else
        echo -e "${RED}Failed to remove rules. You may need to remove '$RULE_FILE' manually.${NC}"
    fi
else
    echo -e "${YELLOW}No permissions found (Skipping).${NC}"
fi

echo -e "${GREEN}[4/4] Removing Installation Files...${NC}"
if [ -d "$SCRIPT_DIR" ]; then
    cd .. || exit 1
    
    rm -rf "$SCRIPT_DIR"
    echo "Deleted $SCRIPT_DIR"
else
    echo -e "${RED}Error: Could not locate installation folder.${NC}"
fi

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}        UNINSTALLATION COMPLETE          ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}You are currently in a deleted directory.${NC}"
echo "Please type 'cd ..' to return to your previous folder."
echo ""
