#!/bin/bash
set -e

VENV_DIR="/home/jacazul/.venv"
REQUIREMENTS_FILE="/home/jacazul/.python/requirements.txt"

# Check if venv exists, create if missing
if [ ! -d "$VENV_DIR/bin" ]; then
    echo "🐍 Creating Python virtual environment at $VENV_DIR..."
    uv venv "$VENV_DIR"
    echo "✓ Virtual environment created successfully"
fi

# Install/update dependencies if requirements.txt exists
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "📦 Installing Python dependencies from $REQUIREMENTS_FILE..."
    # Activate venv and use uv for fast installation
    source "$VENV_DIR/bin/activate"
    
    # Check if uv is available, fallback to pip
    if command -v uv &> /dev/null; then
        uv pip install -r "$REQUIREMENTS_FILE"
        echo "✓ Dependencies installed successfully"
    else
        pip install -r "$REQUIREMENTS_FILE"
        echo "✓ Dependencies installed with pip"
    fi
else
    echo "ℹ️  No requirements.txt found at $REQUIREMENTS_FILE"
fi

# Activate venv before executing copilot
source "$VENV_DIR/bin/activate"

# Execute the copilot command (replace shell process)
exec copilot "$@"
