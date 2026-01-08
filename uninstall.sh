#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "\n${YELLOW}🌙 Moonlight Uninstaller${RESET}"
echo "==================================="

echo -e -n "[*] Removing Desktop Shortcut... "
if [ -f "$HOME/.local/share/applications/Moonlight.desktop" ]; then
    rm "$HOME/.local/share/applications/Moonlight.desktop"
    echo -e "${GREEN}Done${RESET}"
else
    echo -e "${RED}Not Found (Skipping)${RESET}"
fi

echo -e -n "[*] Removing Configuration (~/.config/Moonlight)... "
if [ -d "$HOME/.config/Moonlight" ]; then
    rm -rf "$HOME/.config/Moonlight"
    echo -e "${GREEN}Done${RESET}"
else
    echo -e "${RED}Not Found (Skipping)${RESET}"
fi

RULE_FILE="/etc/udev/rules.d/99-moonlight.rules"
echo -e -n "[*] Checking for udev rules... "
if [ -f "$RULE_FILE" ]; then
    echo -e "${YELLOW}Found${RESET}"
    echo -e "    ${YELLOW}➔ Sudo access required to remove system rules.${RESET}"
    if sudo rm "$RULE_FILE"; then
        echo -e "    ${GREEN}➔ Rules removed.${RESET}"
        
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo -e "    ${GREEN}➔ System permissions reloaded.${RESET}"
    else
        echo -e "    ${RED}➔ Failed to remove rules.${RESET}"
    fi
else
    echo -e "${RED}Not Found (Skipping)${RESET}"
fi

echo -e -n "[*] Removing installation folder... "
if [ -d "$SCRIPT_DIR" ]; then
    cd ..
    rm -rf "$SCRIPT_DIR"
    echo -e "${GREEN}Done${RESET}"
else
    echo -e "${RED}Error: Could not locate folder.${RESET}"
fi

echo "==================================="
echo -e "${GREEN}✨ Moonlight has been completely uninstalled.${RESET}"
echo ""
EOF
chmod +x uninstall.sh
