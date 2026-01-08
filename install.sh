#!/bin/bash
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

TARGET_DIR="$HOME/Moonlight"

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}       Moonlight Setup Assistant         ${NC}"
echo -e "${BLUE}=========================================${NC}"

if [ "$(pwd)" != "$TARGET_DIR" ]; then
    echo -e "${YELLOW}Running from $(pwd). Moving to $TARGET_DIR...${NC}"

    mkdir -p "$TARGET_DIR"
    cp -r ./* "$TARGET_DIR/"
    chmod +x "$TARGET_DIR/install.sh"

    echo -e "${GREEN}Restarting installer from target location...${NC}"

    cd "$TARGET_DIR" || exit 1
    exec ./install.sh
    exit
fi

echo -e "${GREEN}[1/5] Detecting System and Installing Dependencies...${NC}"

if command -v dnf > /dev/null 2>&1; then
    echo "Detected: Fedora/RHEL"
    sudo dnf install -y python3-pip python3-gobject gtk4 libadwaita python3-devel gcc

elif command -v apt-get > /dev/null 2>&1; then
    echo "Detected: Debian/Ubuntu"
    echo "Updating package lists..."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-dev gcc pkg-config

elif command -v pacman > /dev/null 2>&1; then
    echo "Detected: Arch Linux"
    sudo pacman -S --noconfirm python-pip python-gobject gtk4 libadwaita python gcc make

else
    echo -e "${RED}Error: Unsupported package manager.${NC}"
    echo "Please ensure GTK4, LibAdwaita, and Python3 headers are installed."
    read -p "Press Enter to attempt continuing anyway..."
fi

echo -e "${GREEN}[2/5] Installing Python Libraries...${NC}"
pip install --user -r requirements.txt --break-system-packages > /dev/null 2>&1 || pip install --user -r requirements.txt

echo -e "${GREEN}[3/5] Configuring Input Permissions...${NC}"
sudo groupadd -f input
sudo usermod -aG input "$USER"

RULE_FILE="/etc/udev/rules.d/99-moonlight.rules"
echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee "$RULE_FILE" > /dev/null
echo 'KERNEL=="event*", GROUP="input", MODE="0660"' | sudo tee -a "$RULE_FILE" > /dev/null

if command -v udevadm > /dev/null 2>&1; then
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

echo -e "${GREEN}[4/5] Generating Assets...${NC}"

cat <<EOF > start.sh
#!/bin/bash
cd "$TARGET_DIR"
/usr/bin/python3 main.py
EOF
chmod +x start.sh

cat <<EOF > icon.svg
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64px" height="64px" viewBox="0 0 24 24" version="1.1" xmlns="http://www.w3.org/2000/svg">
    <path d="M12.0000002,2.0000002 C12.2855146,2.0000002 12.5649479,2.02237834 12.8373396,2.06546059 C8.97157672,2.67699175 6.00000016,6.02897621 6.00000016,10 C6.00000016,14.4182782 9.58172216,18.0000002 14.0000002,18.0000002 C17.9710241,18.0000002 21.3230086,15.0284236 21.9345398,11.1626607 C21.9776221,11.4350524 22.0000002,11.7144857 22.0000002,12.0000002 C22.0000002,17.5228477 17.5228477,22.0000002 12.0000002,22.0000002 C6.47715266,22.0000002 2.00000016,17.5228477 2.00000016,12.0000002 C2.00000016,6.47715266 6.47715266,2.0000002 12.0000002,2.0000002 Z" fill="#cad3f5" stroke="none"></path>
</svg>
EOF

echo -e "${GREEN}[5/5] Registering Application...${NC}"
mkdir -p ~/.local/share/applications
cat <<EOF > ~/.local/share/applications/moonlight.desktop
[Desktop Entry]
Name=Moonlight
Comment=Auto Clicker
Exec=$TARGET_DIR/start.sh
Icon=$TARGET_DIR/icon.svg
Terminal=false
Type=Application
Categories=Utility;Accessibility;
StartupNotify=true
EOF

echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}        INSTALLATION COMPLETE        ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo "Location: $TARGET_DIR"
echo "Please REBOOT your system to apply input permissions."
