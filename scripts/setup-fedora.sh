#!/bin/bash
# Fedora Setup Script (dnf-based)

DETECT_OS_SCRIPT="$(dirname "$0")/detect-os.sh"

if [ ! -f "$DETECT_OS_SCRIPT" ]; then
    echo "Error: detect-os.sh not found"
    exit 1
fi

bash "$DETECT_OS_SCRIPT"
if [ "$OS_TYPE" != "fedora" ]; then
    printf "\033[1;31mError: This script is for Fedora only. Detected OS: %s\033[0m\n" "$OS_TYPE"
    exit 1
fi

# Commands to check (format: command:package)
COMMANDS=(
    "python3:python3"
    "git:git"
    "gcc:gcc"
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
    "task:task2"
    "bc:bc"
    "node:nodejs"
    "npm:nodejs-npm"
)

MISSING_PACKAGES=()

echo "Checking for missing commands..."
for cmd_pair in "${COMMANDS[@]}"; do
    IFS=':' read -r cmd pkg <<< "$cmd_pair"
    if ! command -v "$cmd" &> /dev/null; then
        echo "  ✗ $cmd (package: $pkg) - MISSING"
        MISSING_PACKAGES+=("$pkg")
    else
        echo "  ✓ $cmd - OK"
    fi
done

if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
    echo "All commands available. No installation needed."
    exit 0
fi

DNF_CMD="dnf install -y"
for pkg in "${MISSING_PACKAGES[@]}"; do
    DNF_CMD="$DNF_CMD $pkg"
done

echo ""
echo "DNF command to be executed:"
echo "$DNF_CMD"
