#!/bin/bash
# Debian Setup Script (apt-based)
# shellcheck source=/dev/null

DETECT_OS_SCRIPT="$(dirname "$0")/detect-os.sh"

if [ ! -f "$DETECT_OS_SCRIPT" ]; then
    echo "Error: detect-os.sh not found"
    exit 1
fi

# shellcheck source=./detect-os.sh
. "$DETECT_OS_SCRIPT"

if [ "$OS_TYPE" != "debian" ] && [ "$OS_TYPE" != "ubuntu" ]; then
    printf "\033[1;31mError: This script is for Debian/Ubuntu only. Detected OS: %s\033[0m\n" "$OS_TYPE"
    exit 1
fi

# Commands to check (format: command:package)
COMMANDS=(
    "python3:python3"
    "git:git"
    "gcc:build-essential"
    "make:make"
    "curl:curl"
    "unzip:unzip"
    "wget:wget"
    "jq:jq"
    "rg:ripgrep"
    "ps:procps"
    "fzf:fzf"
    "htop:htop"
    "sudo:sudo"
    "task:taskwarrior"
    "bc:bc"
    "node:nodejs"
    "npm:npm"
)

# Function to install uv if missing
install_uv() {
    if ! command -v uv &>/dev/null; then
        echo "Installing 'uv' (Python package manager)..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "✅ 'uv' installed successfully via astral.sh"
    else
        echo "✓ uv"
    fi
}

echo "Checking for missing commands on Debian/Ubuntu..."
install_uv
MISSING=()

for cmd_pkg in "${COMMANDS[@]}"; do
    CMD="${cmd_pkg%:*}"
    PKG="${cmd_pkg#*:}"
    if ! command -v "$CMD" &>/dev/null; then
        MISSING+=("$PKG")
    else
        echo "✓ $CMD"
    fi
done

if [ ${#MISSING[@]} -eq 0 ]; then
    echo "All dependencies are already installed."
    exit 0
fi

echo ""
echo "Missing packages: ${MISSING[*]}"
echo ""
echo "To install missing packages, run:"
echo "  sudo apt update && sudo apt install -y ${MISSING[*]}"
exit 1
